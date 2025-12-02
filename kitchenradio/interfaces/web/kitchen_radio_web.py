#!/usr/bin/env python3
"""
Button Controller REST API for KitchenRadio

Exposes a REST API for button control instead of using Raspberry Pi GPIO.
Useful for remote control, testing, and integration with web interfaces.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, TYPE_CHECKING
from flask import Flask, request, jsonify, send_file, render_template
from pathlib import Path
import io
import base64

from kitchenradio.interfaces.hardware.button_controller import ButtonController, ButtonType, ButtonEvent
from kitchenradio.interfaces.hardware.display_controller import DisplayController
from kitchenradio.sources.source_controller import SourceController, SourceType
from kitchenradio.sources.source_model import PlaybackStatus
from kitchenradio.interfaces.hardware.display_interface import DisplayInterface

logger = logging.getLogger(__name__)

class KitchenRadioWeb:
    """
    REST API wrapper for SourceController.
    
    Provides HTTP endpoints for button control and status display.
    Acts as a thin web wrapper around SourceController.
    
    Design:
    - Accepts external SourceController, DisplayController, and ButtonController
    - Does not create or own these components (they're managed by the daemon)
    - Provides REST API endpoints to interact with existing controllers
    - Minimal initialization - just sets up Flask routes
    """
    
    def __init__(self, 
                 source_controller: 'SourceController',
                 display_controller = None,
                 button_controller = None,
                 kitchen_radio = None,
                 host: str = '0.0.0.0',
                 port: int = 5001):
        """
        Initialize KitchenRadio Web API as a wrapper around existing components.
        
        Args:
            source_controller: SourceController instance to control (REQUIRED)
            display_controller: Optional DisplayController instance for display API
            button_controller: Optional ButtonController instance for button API
            kitchen_radio: Optional KitchenRadio instance for daemon operations (reconnect_backends)
            host: API server host address (default: 0.0.0.0 = all interfaces)
            port: API server port (default: 5001)
            
        Note:
            This class uses SourceController directly instead of KitchenRadio facade.
            All UI components now use SourceController for cleaner architecture.
            KitchenRadio reference is only kept for daemon-level operations like reconnect_backends.
        """
        # Store references to external components
        if source_controller is None:
            raise ValueError("source_controller is required - KitchenRadioWeb is now a wrapper and does not create its own instance")
        
        self.source_controller = source_controller
        self.display_controller = display_controller
        self.button_controller = button_controller
        self.kitchen_radio = kitchen_radio  # Optional, only for daemon operations
        
        # Store display interface reference if available
        self.display_interface = display_controller.display_interface if display_controller else None
            
        self.host = host
        self.port = port
 
        # Flask app for REST API
        # Use absolute paths to templates/static folders
        # Path structure: KitchenRadio/kitchenradio/interfaces/web/kitchen_radio_web.py
        # We need to go up 4 levels: web -> interfaces -> kitchenradio -> KitchenRadio
        base_dir = Path(__file__).resolve().parent.parent.parent.parent  # Go up to KitchenRadio root
        template_dir = base_dir / 'frontend' / 'templates'
        static_dir = base_dir / 'frontend' / 'static'
        
        logger.info(f"Flask template directory: {template_dir}")
        logger.info(f"Flask static directory: {static_dir}")
        logger.info(f"Template directory exists: {template_dir.exists()}")
        logger.info(f"Static directory exists: {static_dir.exists()}")
        
        self.app = Flask(__name__, 
                        template_folder=str(template_dir),
                        static_folder=str(static_dir))
        self.app.logger.setLevel(logging.WARNING)  # Reduce Flask noise
        
        # Setup routes
        self._setup_routes()
        
        # API state
        self.running = False
        self.server_thread = None
        
        # Button press statistics
        self.button_stats = {button.value: 0 for button in ButtonType}
        self.last_button_press = None
        self.api_start_time = None
        
    def _get_status_dict(self):
        """Helper to construct status dict from DisplayController cache"""
        if not self.display_controller:
            return {}
            
        # Use cached state from DisplayController to avoid direct SourceController access
        playback_state = self.display_controller.cached_playback_state
        track_info = self.display_controller.cached_track_info
        source_info = self.display_controller.cached_source_info
        current_source = self.display_controller.cached_current_source
        powered_on = self.display_controller.cached_powered_on
        available_sources = self.display_controller.cached_available_sources
        
        # Derive connection status from available sources
        mpd_connected = 'mpd' in available_sources
        librespot_connected = 'librespot' in available_sources
        
        return {
            'current_source': current_source,
            'powered_on': powered_on,
            'available_sources': available_sources,
            'playback_state': playback_state.to_dict() if playback_state else {},
            'track_info': track_info.to_dict() if track_info else {},
            'source_info': source_info.to_dict() if source_info else {},
            # Legacy fields for compatibility
            'mpd': {
                'connected': mpd_connected,
                'state': playback_state.status.value if current_source == 'mpd' else 'stopped',
                'volume': playback_state.volume if current_source == 'mpd' else 0,
                'current_track': track_info.to_dict() if track_info and current_source == 'mpd' else {}
            },
            'librespot': {
                'connected': librespot_connected,
                'state': playback_state.status.value if current_source == 'librespot' else 'stopped',
                'volume': playback_state.volume if current_source == 'librespot' else 0,
                'current_track': track_info.to_dict() if track_info and current_source == 'librespot' else {}
            }
        }
        
    def _setup_routes(self):
        """Setup Flask routes for the API"""
        
        # Radio Interface Routes
        @self.app.route('/')
        def index():
            """Redirect to radio interface"""
            return render_template('radio_interface.html')
        
        @self.app.route('/radio')
        def radio_interface():
            """Serve the physical radio interface"""
            return render_template('radio_interface.html')
        
        @self.app.route('/api/buttons', methods=['GET'])
        def list_buttons():
            """List all available buttons"""
            buttons = []
            for button_type in ButtonType:
                buttons.append({
                    'name': button_type.value,
                    'description': self._get_button_description(button_type),
                    'category': self._get_button_category(button_type),
                    'press_count': self.button_stats[button_type.value]
                })
            
            return jsonify({
                'buttons': buttons,
                'total_buttons': len(buttons),
                'button_controller_available': self.button_controller is not None
            })
        
        @self.app.route('/api/button/<button_name>', methods=['POST'])
        def press_button(button_name: str):
            """Press a specific button"""
            try:
                # Validate button name
                button_type = None
                for bt in ButtonType:
                    if bt.value == button_name:
                        button_type = bt
                        break
                
                if not button_type:
                    return jsonify({
                        'success': False,
                        'error': f'Unknown button: {button_name}',
                        'available_buttons': [bt.value for bt in ButtonType]
                    }), 400
                
                # Check if button controller is available
                if not self.button_controller:
                    return jsonify({
                        'success': False,
                        'error': 'Button controller not available',
                        'message': 'Web interface started without button controller'
                    }), 503
                
                # Press the button
                result = self.button_controller.press_button(button_name)
                
                # Update statistics
                self.button_stats[button_name] += 1
                self.last_button_press = {
                    'button': button_name,
                    'timestamp': time.time(),
                    'success': result
                }
                
                # If it's a source button and the press was successful, the SourceController
                # will emit an event which the DisplayController will pick up.
                # No manual display update needed here.
                
                logger.info(f"API button press: {button_name} -> {result}")
                
                return jsonify({
                    'success': result,
                    'button': button_name,
                    'timestamp': time.time(),
                    'message': f'Button {button_name} pressed successfully' if result else f'Button {button_name} press failed'
                })
                
            except Exception as e:
                logger.error(f"Error pressing button {button_name}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'button': button_name
                }), 500
        
        @self.app.route('/api/button/<button_name>/info', methods=['GET'])
        def button_info(button_name: str):
            """Get information about a specific button"""
            button_type = None
            for bt in ButtonType:
                if bt.value == button_name:
                    button_type = bt
                    break
            
            if not button_type:
                return jsonify({
                    'error': f'Unknown button: {button_name}'
                }), 404
            
            # Get GPIO pin if button controller is available
            gpio_pin = 'N/A'
            if self.button_controller and hasattr(self.button_controller, 'pin_mapping'):
                gpio_pin = self.button_controller.pin_mapping.get(button_type, 'N/A')
            
            return jsonify({
                'name': button_name,
                'description': self._get_button_description(button_type),
                'category': self._get_button_category(button_type),
                'press_count': self.button_stats[button_name],
                'gpio_pin': gpio_pin,
                'button_controller_available': self.button_controller is not None
            })
        
        
        @self.app.route('/api/buttons/stats', methods=['GET'])
        def button_stats():
            """Get button press statistics"""
            total_presses = sum(self.button_stats.values())
            
            return jsonify({
                'button_stats': self.button_stats,
                'total_presses': total_presses,
                'last_button_press': self.last_button_press,
                'api_uptime': time.time() - self.api_start_time if self.api_start_time else 0,
                'button_controller_available': self.button_controller is not None
            })
        
        @self.app.route('/api/buttons/reset-stats', methods=['POST'])
        def reset_stats():
            """Reset button press statistics"""
            self.button_stats = {button.value: 0 for button in ButtonType}
            self.last_button_press = None
            
            return jsonify({
                'success': True,
                'message': 'Button statistics reset'
            })
        
        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            """Get API status and SourceController status"""
            kitchen_status = self._get_status_dict()
            
            return jsonify({
                'api_running': self.running,
                'api_uptime': time.time() - self.api_start_time if self.api_start_time else 0,
                'components': {
                    'kitchen_radio': True,
                    'button_controller': self.button_controller is not None,
                    'display_controller': self.display_controller is not None,
                    'display_interface': self.display_interface is not None
                },
                'total_button_presses': sum(self.button_stats.values()),
                'kitchen_radio': kitchen_status
            })
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'api_version': '1.0.0'
            })
        
        @self.app.route('/api/reconnect', methods=['POST'])
        def reconnect_backends():
            """Attempt to reconnect to disconnected backends"""
            try:
                if not self.kitchen_radio:
                    return jsonify({
                        'success': False,
                        'message': 'KitchenRadio instance not available for reconnect operation',
                        'timestamp': time.time()
                    }), 503
                
                results = self.kitchen_radio.reconnect_backends()
                return jsonify({
                    'success': True,
                    'reconnection_results': results,
                    'message': 'Reconnection attempt completed',
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error during backend reconnection: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Display API endpoints
        @self.app.route('/api/display/image', methods=['GET'])
        def get_display_image():
            """Get current display image as BMP"""
            try:
                if not self.display_interface:
                    return jsonify({'error': 'Display interface not available'}), 503
                
                # Check if display supports image export
                if not hasattr(self.display_interface, 'getDisplayImage'):
                    return jsonify({'error': 'Display image export not supported'}), 503
                    
                # Get BMP data from display interface
                bmp_data = self.display_interface.getDisplayImage()
                if bmp_data:
                    # Return BMP data directly
                    img_buffer = io.BytesIO(bmp_data)
                    img_buffer.seek(0)
                    
                    return send_file(
                        img_buffer,
                        mimetype='image/bmp',
                        as_attachment=False,
                        download_name='display.bmp'
                    )
                else:
                    return jsonify({'error': 'No display image available'}), 404
                    
            except Exception as e:
                logger.error(f"Error getting display image: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/display/ascii', methods=['GET'])
        def get_display_ascii():
            """Get current display as ASCII art"""
            try:
                if not self.display_interface:
                    return jsonify({'error': 'Display interface not available'}), 503
                
                # Check if display supports ASCII export (emulator mode has this)
                if not hasattr(self.display_interface, 'get_ascii_representation'):
                    return jsonify({'error': 'ASCII display export only available in emulator mode'}), 503
                    
                ascii_art = self.display_interface.get_ascii_representation()
                return jsonify({
                    'ascii_art': ascii_art,
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error getting display ASCII: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/display/clear', methods=['POST'])
        def clear_display():
            """Clear the display"""
            try:
                if not self.display_interface:
                    return jsonify({'error': 'Display interface not available'}), 503
                    
                self.display_interface.clear()
                return jsonify({
                    'success': True,
                    'message': 'Display cleared',
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error clearing display: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/display/test', methods=['POST'])
        def test_display():
            """Show test pattern on display"""
            try:
                if not self.display_interface:
                    return jsonify({'error': 'Display interface not available'}), 503
                
                # Check if display interface has test_display method
                if hasattr(self.display_interface, 'display_test_pattern'):
                    result = self.display_interface.display_test_pattern()
                elif hasattr(self.display_interface, 'test_display'):
                    result = self.display_interface.test_display()
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Test pattern not supported by this display interface',
                        'timestamp': time.time()
                    })
                    
                return jsonify({
                    'success': result,
                    'message': 'Test pattern displayed' if result else 'Test pattern failed',
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error showing test pattern: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/display/stats', methods=['GET'])
        def display_stats():
            """Get display statistics and info"""
            try:
                if not self.display_interface:
                    return jsonify({'error': 'Display interface not available'}), 503
                
                result = {}
                
                # Get display info (available on all display interfaces)
                if hasattr(self.display_interface, 'get_display_info'):
                    result['display_info'] = self.display_interface.get_display_info()
                else:
                    result['display_info'] = {
                        'type': type(self.display_interface).__name__,
                        'size': self.display_interface.get_size() if hasattr(self.display_interface, 'get_size') else 'unknown',
                        'initialized': self.display_interface.is_initialized() if hasattr(self.display_interface, 'is_initialized') else 'unknown'
                    }
                
                # Get statistics if available (emulator mode has this)
                if hasattr(self.display_interface, 'get_statistics'):
                    result['display_stats'] = self.display_interface.get_statistics()
                
                result['timestamp'] = time.time()
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error getting display stats: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/display/status', methods=['GET'])
        def display_status():
            """Get display controller and interface status"""
            try:
                status = {
                    'interface_available': self.display_interface is not None,
                    'interface_type': type(self.display_interface).__name__ if self.display_interface else None,
                    'controller_available': self.display_controller is not None,
                    'timestamp': time.time()
                }
                
                # Add mode information if available
                if self.display_interface and hasattr(self.display_interface, 'get_mode'):
                    status['display_mode'] = self.display_interface.get_mode()
                    status['is_hardware'] = self.display_interface.is_hardware_mode() if hasattr(self.display_interface, 'is_hardware_mode') else False
                    status['is_emulator'] = self.display_interface.is_emulator_mode() if hasattr(self.display_interface, 'is_emulator_mode') else False
                
                # Add detailed interface information
                if self.display_interface:
                    if hasattr(self.display_interface, 'get_display_info'):
                        status['interface_info'] = self.display_interface.get_display_info()
                    if hasattr(self.display_interface, 'get_statistics'):
                        status['interface_stats'] = self.display_interface.get_statistics()
                    if hasattr(self.display_interface, 'is_initialized'):
                        status['interface_initialized'] = self.display_interface.is_initialized()
                
                status['controller_initialized'] = self.display_controller is not None
                    
                return jsonify(status)
            except Exception as e:
                logger.error(f"Error getting display status: {e}")
                return jsonify({'error': str(e)}), 500
        

        @self.app.route('/api/display/update', methods=['POST'])
        def update_display():
            """Update display with current SourceController status"""
            try:
                if self.display_controller:
                    self.display_controller.request_update()
                    return jsonify({
                        'success': True,
                        'message': 'Display update requested',
                        'timestamp': time.time()
                    })
                else:
                    return jsonify({'error': 'Display controller not available'}), 503
                    
            except Exception as e:
                logger.error(f"Error updating display: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/display/show_text', methods=['POST'])
        def show_text_on_display():
            """Show custom text on display"""
            try:
                if not self.display_controller:
                    return jsonify({'error': 'Display controller not available'}), 503
                
                # Get text from request
                data = request.get_json() or {}
                main_text = data.get('main_text', 'KitchenRadio')
                sub_text = data.get('sub_text', '')
                
                # Use DisplayController to show notification/text
                self.display_controller.show_Notification_overlay(main_text, sub_text)
                
                return jsonify({
                    'success': True,
                    'message': f'Text displayed: "{main_text}"',
                    'main_text': main_text,
                    'sub_text': sub_text,
                    'timestamp': time.time()
                })
                    
            except Exception as e:
                logger.error(f"Error showing text on display: {e}")
                return jsonify({'error': str(e)}), 500

        # ...existing code...
        
    def _get_button_description(self, button_type: ButtonType) -> str:
        """Get human-readable description for a button"""
        descriptions = {
            ButtonType.SOURCE_MPD: "Switch to MPD music source",
            ButtonType.SOURCE_SPOTIFY: "Switch to Spotify music source",
            ButtonType.TRANSPORT_PLAY_PAUSE: "Toggle play/pause",
            ButtonType.TRANSPORT_STOP: "Stop playback",
            ButtonType.TRANSPORT_NEXT: "Next track",
            ButtonType.TRANSPORT_PREVIOUS: "Previous track",
            ButtonType.VOLUME_UP: "Increase volume",
            ButtonType.VOLUME_DOWN: "Decrease volume",
            ButtonType.MENU_UP: "Navigate menu up",
            ButtonType.MENU_DOWN: "Navigate menu down",
            ButtonType.SLEEP: "Sleep",              
            ButtonType.REPEAT: "Repeat",           
            ButtonType.SHUFFLE: "Shuffle",          
            ButtonType.DISPLAY: "Display", 
            ButtonType.POWER: "Power button - stop all playback"
        }
        return descriptions.get(button_type, "Unknown button")
    
    def _get_button_category(self, button_type: ButtonType) -> str:
        """Get category for a button"""
        if button_type in [ButtonType.SOURCE_MPD, ButtonType.SOURCE_SPOTIFY]:
            return "source"
        elif button_type in [ButtonType.TRANSPORT_PLAY_PAUSE, ButtonType.TRANSPORT_STOP, 
                           ButtonType.TRANSPORT_NEXT, ButtonType.TRANSPORT_PREVIOUS]:
            return "transport"
        elif button_type in [ButtonType.VOLUME_UP, ButtonType.VOLUME_DOWN]:
            return "volume"
        elif button_type in [ButtonType.MENU_UP, ButtonType.MENU_DOWN]:
            return "menu"
        elif button_type == ButtonType.POWER:
            return "power"
        else:
            return "other"
    
    def start(self) -> bool:
        """
        Start the KitchenRadio Web API server.
        
        Note:
            This only starts the Flask web server. It does NOT initialize
            KitchenRadio, DisplayController, or ButtonController - those should
            already be initialized by the caller/daemon before calling this.
        
        Returns:
            True if started successfully
        """
        try:
            # Verify kitchen_radio is running (it should be started by caller)
            if not self.kitchen_radio:
                logger.error("No KitchenRadio instance provided - cannot start web API")
                return False
            
            # Log what components are available
            logger.info("Starting KitchenRadio Web API with:")
            logger.info(f"  - KitchenRadio: {'✓' if self.kitchen_radio else '✗'}")
            logger.info(f"  - DisplayController: {'✓' if self.display_controller else '✗'}")
            logger.info(f"  - ButtonController: {'✓' if self.button_controller else '✗'}")
            logger.info(f"  - DisplayInterface: {'✓' if self.display_interface else '✗'}")
            
            # Start API server in background thread
            self.running = True
            self.api_start_time = time.time()
            
            def run_server():
                try:
                    self.app.run(
                        host=self.host,
                        port=self.port,
                        debug=False,
                        use_reloader=False,
                        threaded=True
                    )
                except Exception as e:
                    logger.error(f"API server error: {e}")
                    self.running = False
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # Give server time to start
            time.sleep(0.5)
            
            logger.info(f"✓ KitchenRadio Web API started on http://{self.host}:{self.port}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start KitchenRadio Web API: {e}")
            return False
    
    def stop(self):
        """
        Stop the KitchenRadio Web API server.
        
        Note:
            This only stops the Flask web server. It does NOT clean up
            KitchenRadio, DisplayController, or ButtonController - those
            should be cleaned up by the caller/daemon that created them.
        """
        logger.info("Stopping KitchenRadio Web API...")
        
        self.running = False
        
        # Note: Flask development server doesn't have a clean shutdown method
        # In production, you'd use a proper WSGI server like Gunicorn
        
        logger.info("✓ KitchenRadio Web API stopped")
    
    def press_button_direct(self, button_name: str) -> bool:
        """
        Directly press a button (bypass API).
        
        Args:
            button_name: Name of button to press
            
        Returns:
            True if successful
        """
        if not self.button_controller:
            logger.warning("No button controller available - cannot press button")
            return False
        return self.button_controller.press_button(button_name)


# Example usage and testing
if __name__ == "__main__":
    import sys
    import os
    import signal
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("KitchenRadio Web API - Standalone Test Mode")
    print("="*60)
    print("\nNOTE: KitchenRadioWeb is now a wrapper that requires")
    print("      pre-configured KitchenRadio + controllers.")
    print("\nFor proper usage, use: python run_daemon.py --web")
    print("\nThis standalone mode creates minimal components for testing.")
    print("="*60)
    
    # Create components for standalone testing
    print("\n1. Creating KitchenRadio instance...")
    from kitchenradio.kitchen_radio import KitchenRadio
    kitchen_radio = KitchenRadio()
    
    print("2. Starting KitchenRadio...")
    if not kitchen_radio.start():
        print("ERROR: Failed to start KitchenRadio")
        sys.exit(1)
    
    # Get SourceController from KitchenRadio
    source_controller = kitchen_radio.source_controller
    
    print("3. Creating DisplayInterface (emulator mode)...")
    display_interface = DisplayInterface(use_hardware=False)
    display_interface.initialize()
    
    print("4. Creating DisplayController...")
    display_controller = DisplayController(
        source_controller=source_controller,
        display_interface=display_interface
    )
    display_controller.initialize()
    
    print("5. Creating ButtonController (software mode)...")
    button_controller = ButtonController(
        source_controller=source_controller,
        display_controller=display_controller,
        use_hardware=False  # Software mode for testing
    )
    button_controller.initialize()
    
    print("6. Creating KitchenRadioWeb wrapper...")
    api = KitchenRadioWeb(
        source_controller=source_controller,
        display_controller=display_controller,
        button_controller=button_controller,
        kitchen_radio=kitchen_radio,  # For reconnect_backends
        host='0.0.0.0',
        port=5001
    )
    
    # Signal handler for cleanup
    def signal_handler(signum, frame):
        logger.info(f"Web API received signal {signum}, initiating shutdown...")
        api.running = False
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if api.start():
        print("\n" + "="*60)
        print("✓ KitchenRadio Web API started successfully!")
        print("="*60)
        print("\nAPI available at:")
        print("  - Local:   http://127.0.0.1:5001")
        print("  - Network: http://<your-ip>:5001")
        print("  (Use 'ipconfig' to find your IP address)")
        print("\nAvailable endpoints:")
        print("  Radio Interface:")
        print("    GET  / - Main radio interface")
        print("    GET  /radio - Alternative radio interface")
        print("  Button Control:")
        print("    GET  /api/buttons - List all buttons")
        print("    POST /api/button/<name> - Press a button")
        print("    GET  /api/button/<name>/info - Get button info")
        print("    GET  /api/buttons/stats - Get button statistics")
        print("  Display Control:")
        print("    GET  /api/display/image - Get display image (BMP)")
        print("    GET  /api/display/ascii - Get display as ASCII art")
        print("    POST /api/display/update - Update display with status")
        print("    GET  /api/display/status - Get display status")
        print("  System:")
        print("    GET  /api/status - Get API and radio status")
        print("    GET  /api/health - Health check")
        print("    POST /api/reconnect - Reconnect backends")
        print("\nPress Ctrl+C to stop")
        print("="*60)
        
        try:
            # Keep running
            while api.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            print("Stopping web API...")
            api.stop()
            print("Cleaning up components...")
            display_controller.cleanup()
            button_controller.cleanup()
            display_interface.cleanup()
            kitchen_radio.stop()
            print("✓ Shutdown complete")
    else:
        print("ERROR: Failed to start KitchenRadio Web API")
        sys.exit(1)
