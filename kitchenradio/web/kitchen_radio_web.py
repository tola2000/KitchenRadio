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

from kitchenradio.radio.hardware.button_controller import ButtonController, ButtonType, ButtonEvent
from kitchenradio.web.display_interface_emulator import DisplayInterfaceEmulator

if TYPE_CHECKING:
    from ..radio.kitchen_radio import KitchenRadio

logger = logging.getLogger(__name__)

# Try to import display controller and emulator with graceful fallback
try:
    from ..radio.hardware.display_controller import DisplayController
except ImportError as e:
    logger.warning(f"DisplayController not available: {e}")
    DisplayController = None

try:
    from .display_interface_emulator import EmulatorDisplayInterface
    logger.info("EmulatorDisplayInterface imported successfully")
except ImportError as e:
    logger.error(f"Failed to import EmulatorDisplayInterface: {e}")
    EmulatorDisplayInterface = None
except Exception as e:
    logger.error(f"Unexpected error importing EmulatorDisplayInterface: {e}")
    EmulatorDisplayInterface = None


class KitchenRadioWeb:
    """
    REST API wrapper for ButtonController.
    
    Provides HTTP endpoints for button control instead of GPIO pins.
    Can be used alongside or instead of physical GPIO buttons.
    """
    
    def __init__(self, 
                 kitchen_radio: 'KitchenRadio' = None,
                 host: str = '0.0.0.0',
                 port: int = 5001,
                 enable_gpio: bool = False):
        """
        Initialize KitchenRadio Web API.
        
        Args:
            kitchen_radio: KitchenRadio instance to control (will create if None)
            host: API server host address
            port: API server port
            enable_gpio: Whether to also enable GPIO buttons
        """
        # Create or use provided KitchenRadio instance
        if kitchen_radio is None:
            from kitchenradio.radio.kitchen_radio import KitchenRadio
            self.kitchen_radio = KitchenRadio()
            self._owns_kitchen_radio = True
        else:
            self.kitchen_radio = kitchen_radio
            self._owns_kitchen_radio = False
            
        self.host = host
        self.port = port
        self.enable_gpio = enable_gpio
        
        # Create underlying button controller
        self.button_controller = ButtonController(self.kitchen_radio)
        

        self.display_emulator = DisplayInterfaceEmulator()
        self.display_emulator.initialize()
        logger.info("Display emulator initialized successfully")

        # Initialize display controller using the emulator as the interface
        if DisplayController and self.display_emulator:
            try:
                # Create display controller with emulator as the I2C interface and kitchen_radio
                self.display_controller = DisplayController(
                    kitchen_radio=self.kitchen_radio,
                    i2c_interface=self.display_emulator
                )
                self.display_controller.initialize()
                logger.info("Display controller initialized with emulator interface and update loop started")
            except Exception as e:
                logger.warning(f"Failed to initialize display controller with emulator: {e}")
                self.display_controller = None
        else:
            self.display_controller = None
            if not DisplayController:
                logger.info("Display controller not available - using emulator only")
            elif not self.display_emulator:
                logger.info("Display controller disabled - no emulator interface available")
                logger.info("Display controller not available - using emulator only")
            elif not self.display_emulator:
                logger.info("Display controller disabled - no emulator interface available")


        # Flask app for REST API
        self.app = Flask(__name__, 
                        template_folder='../../frontend/templates',
                        static_folder='../../frontend/static')
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
                'gpio_enabled': self.enable_gpio
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
                
                # Press the button
                result = self.button_controller.press_button(button_name)
                
                # Update statistics
                self.button_stats[button_name] += 1
                self.last_button_press = {
                    'button': button_name,
                    'timestamp': time.time(),
                    'success': result
                }
                
                # If it's a source button and the press was successful, update the display
                if result and button_name in ['source_mpd', 'source_spotify'] and self.display_emulator:
                    try:
                        from kitchenradio.radio.hardware.display_formatter import DisplayFormatter
                        formatter = DisplayFormatter()
                        status_data = self.kitchen_radio.get_status()
                        draw_func = formatter.format_status(status_data)
                        self.display_emulator.render_frame(draw_func)
                        logger.info(f"Display updated after {button_name} press")
                    except Exception as display_error:
                        logger.warning(f"Failed to update display after {button_name}: {display_error}")
                
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
            
            return jsonify({
                'name': button_name,
                'description': self._get_button_description(button_type),
                'category': self._get_button_category(button_type),
                'press_count': self.button_stats[button_name],
                'gpio_pin': self.button_controller.pin_mapping.get(button_type, 'N/A') if self.enable_gpio else 'N/A'
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
                'gpio_enabled': self.enable_gpio
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
            """Get API status and KitchenRadio status"""
            kitchen_status = self.kitchen_radio.get_status()
            
            return jsonify({
                'api_running': self.running,
                'api_uptime': time.time() - self.api_start_time if self.api_start_time else 0,
                'gpio_enabled': self.enable_gpio,
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
                if not self.display_emulator:
                    return jsonify({'error': 'Display emulator not available'}), 503
                    
                # Get BMP data from emulator
                bmp_data = self.display_emulator.getDisplayImage()
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
                if not self.display_emulator:
                    return jsonify({'error': 'Display emulator not available'}), 503
                    
                ascii_art = self.display_emulator.get_ascii_representation()
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
                if not self.display_emulator:
                    return jsonify({'error': 'Display emulator not available'}), 503
                    
                self.display_emulator.clear()
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
                if not self.display_emulator:
                    return jsonify({'error': 'Display emulator not available'}), 503
                    
                result = self.display_emulator.test_display()
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
                if not self.display_emulator:
                    return jsonify({'error': 'Display emulator not available'}), 503
                    
                stats = self.display_emulator.get_statistics()
                info = self.display_emulator.get_display_info()
                return jsonify({
                    'display_info': info,
                    'display_stats': stats,
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error getting display stats: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/display/status', methods=['GET'])
        def display_status():
            """Get display controller and emulator status"""
            try:
                status = {
                    'emulator_available': self.display_emulator is not None,
                    'controller_available': self.display_controller is not None,
                    'timestamp': time.time()
                }
                
                if self.display_emulator:
                    status['emulator_info'] = self.display_emulator.get_display_info()
                    status['emulator_stats'] = self.display_emulator.get_statistics()
                
                if self.display_controller:
                    status['controller_initialized'] = True
                    # Add any display controller specific status here
                else:
                    status['controller_initialized'] = False
                    
                return jsonify(status)
            except Exception as e:
                logger.error(f"Error getting display status: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Menu API endpoints
        @self.app.route('/api/menu', methods=['GET'])
        def get_menu():
            """Get menu options for the active source"""
            try:
                # Get current source from KitchenRadio
                status = self.kitchen_radio.get_status()
                active_source = status.get('current_source', 'none')
                available_sources = status.get('available_sources', [])
                
                if active_source == 'mpd' and 'mpd' in available_sources:
                    # MPD menu - playlists
                    menu_items = [
                        {'id': 'playlist_1', 'label': 'Classic Rock', 'type': 'playlist'},
                        {'id': 'playlist_2', 'label': 'Jazz Collection', 'type': 'playlist'},
                        {'id': 'playlist_3', 'label': 'Electronic', 'type': 'playlist'},
                        {'id': 'playlist_4', 'label': 'Ambient', 'type': 'playlist'},
                    ]
                elif active_source == 'spotify' and 'librespot' in available_sources:
                    # Spotify menu - settings
                    menu_items = [
                        {'id': 'shuffle', 'label': 'Shuffle: Off', 'type': 'toggle'},
                        {'id': 'repeat', 'label': 'Repeat: Off', 'type': 'cycle'},
                        {'id': 'quality', 'label': 'Quality: High', 'type': 'setting'},
                    ]
                elif not available_sources:
                    # No backends available
                    menu_items = [
                        {'id': 'no_backends', 'label': 'No backends connected', 'type': 'info'},
                        {'id': 'reconnect', 'label': 'Try reconnecting...', 'type': 'action'},
                    ]
                else:
                    # No source selected but backends available
                    menu_items = [
                        {'id': 'select_source', 'label': 'Select a source first', 'type': 'info'},
                    ]
                    # Add available sources as options
                    if 'mpd' in available_sources:
                        menu_items.append({'id': 'switch_to_mpd', 'label': 'Switch to MPD', 'type': 'action'})
                    if 'librespot' in available_sources:
                        menu_items.append({'id': 'switch_to_spotify', 'label': 'Switch to Spotify', 'type': 'action'})
                
                return jsonify({
                    'active_source': active_source,
                    'available_sources': available_sources,
                    'menu_items': menu_items,
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error getting menu: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/menu/action', methods=['POST'])
        def menu_action():
            """Execute a menu action"""
            try:
                data = request.get_json()
                action = data.get('action')
                item_id = data.get('item_id')
                
                logger.info(f"Menu action: {action} on item {item_id}")
                
                # Handle special actions
                if action == 'select' and item_id:
                    if item_id == 'reconnect':
                        # Attempt to reconnect backends
                        results = self.kitchen_radio.reconnect_backends()
                        return jsonify({
                            'success': True,
                            'message': 'Reconnection attempted',
                            'action': 'backends_reconnected',
                            'results': results
                        })
                    elif item_id == 'switch_to_mpd':
                        # Switch to MPD source
                        from ..radio.kitchen_radio import BackendType
                        try:
                            success = self.kitchen_radio.set_source(BackendType.MPD)
                            return jsonify({
                                'success': success,
                                'message': 'Switched to MPD' if success else 'Failed to switch to MPD',
                                'action': 'source_changed'
                            })
                        except Exception as e:
                            return jsonify({
                                'success': False,
                                'message': f'Error switching to MPD: {e}',
                                'action': 'source_change_failed'
                            })
                    elif item_id == 'switch_to_spotify':
                        # Switch to Spotify source
                        from ..radio.kitchen_radio import BackendType
                        try:
                            success = self.kitchen_radio.set_source(BackendType.LIBRESPOT)
                            return jsonify({
                                'success': success,
                                'message': 'Switched to Spotify' if success else 'Failed to switch to Spotify',
                                'action': 'source_changed'
                            })
                        except Exception as e:
                            return jsonify({
                                'success': False,
                                'message': f'Error switching to Spotify: {e}',
                                'action': 'source_change_failed'
                            })
                    elif item_id.startswith('playlist_'):
                        # Load playlist
                        return jsonify({
                            'success': True,
                            'message': f'Playlist {item_id} loaded',
                            'action': 'playlist_loaded'
                        })
                    elif item_id == 'shuffle':
                        # Toggle shuffle
                        return jsonify({
                            'success': True,
                            'message': 'Shuffle toggled',
                            'action': 'shuffle_toggled'
                        })
                    elif item_id == 'repeat':
                        # Cycle repeat mode
                        return jsonify({
                            'success': True,
                            'message': 'Repeat mode changed',
                            'action': 'repeat_cycled'
                        })
                
                return jsonify({
                    'success': True,
                    'message': f'Action {action} executed',
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error executing menu action: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/display/update', methods=['POST'])
        def update_display():
            """Update display with current KitchenRadio status"""
            try:
                if not self.display_emulator:
                    return jsonify({'error': 'Display emulator not available'}), 503
                
                # Get current status from KitchenRadio
                status_data = self.kitchen_radio.get_status()
                
                # Import display formatter here to avoid circular imports
                try:
                    from kitchenradio.radio.hardware.display_formatter import DisplayFormatter
                    formatter = DisplayFormatter()
                    
                    # Format status for display
                    draw_func = formatter.format_status(status_data)
                    
                    # Render to emulator
                    result = self.display_emulator.render_frame(draw_func)
                    
                    return jsonify({
                        'success': result,
                        'message': 'Display updated with current status' if result else 'Display update failed',
                        'status_data': status_data,
                        'timestamp': time.time()
                    })
                    
                except ImportError as e:
                    return jsonify({
                        'error': f'Display formatter not available: {e}',
                        'success': False
                    }), 503
                    
            except Exception as e:
                logger.error(f"Error updating display: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/display/show_text', methods=['POST'])
        def show_text_on_display():
            """Show custom text on display"""
            try:
                if not self.display_emulator:
                    return jsonify({'error': 'Display emulator not available'}), 503
                
                # Get text from request
                data = request.get_json() or {}
                main_text = data.get('main_text', 'KitchenRadio')
                sub_text = data.get('sub_text', '')
                
                # Import display formatter
                try:
                    from kitchenradio.radio.hardware.display_formatter import DisplayFormatter
                    formatter = DisplayFormatter()
                    
                    # Format text for display
                    draw_func = formatter.format_simple_text(main_text, sub_text)
                    
                    # Render to emulator
                    result = self.display_emulator.render_frame(draw_func)
                    
                    return jsonify({
                        'success': result,
                        'message': f'Text displayed: "{main_text}"' if result else 'Text display failed',
                        'main_text': main_text,
                        'sub_text': sub_text,
                        'timestamp': time.time()
                    })
                    
                except ImportError as e:
                    return jsonify({
                        'error': f'Display formatter not available: {e}',
                        'success': False
                    }), 503
                    
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
            ButtonType.MENU_OK: "Select menu item",
            ButtonType.MENU_EXIT: "Exit menu",
            ButtonType.MENU_TOGGLE: "Toggle menu display",
            ButtonType.MENU_SET: "Confirm menu selection",
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
        elif button_type in [ButtonType.MENU_UP, ButtonType.MENU_DOWN, ButtonType.MENU_OK,
                           ButtonType.MENU_EXIT, ButtonType.MENU_TOGGLE, ButtonType.MENU_SET]:
            return "menu"
        elif button_type == ButtonType.POWER:
            return "power"
        else:
            return "other"
    
    def start(self) -> bool:
        """
        Start the KitchenRadio Web API server.
        
        Returns:
            True if started successfully
        """
        try:
            # Start KitchenRadio if we own it
            if self._owns_kitchen_radio:
                if not self.kitchen_radio.start():
                    logger.error("Failed to start KitchenRadio instance")
                    return False
            
            # Initialize display emulator
            if self.display_emulator:
                if not self.display_emulator.initialize():
                    logger.warning("Failed to initialize display emulator, continuing anyway")
            else:
                logger.info("Display emulator not available - display features disabled")
            
            # Note: Display controller would need hardware - using emulator directly for now
            
            # Initialize underlying button controller (for GPIO if enabled)
            if self.enable_gpio:
                if not self.button_controller.initialize():
                    logger.warning("Failed to initialize GPIO buttons, continuing with API only")
            
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
            
            logger.info(f"KitchenRadio Web API started on http://{self.host}:{self.port}")
            logger.info(f"GPIO buttons {'enabled' if self.enable_gpio else 'disabled'}")
            logger.info(f"Display emulator available: {self.display_emulator is not None}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start KitchenRadio Web API: {e}")
            return False
    
    def stop(self):
        """Stop the KitchenRadio Web API server"""
        logger.info("Stopping KitchenRadio Web API...")
        
        self.running = False
        
        # Cleanup display emulator
        if self.display_emulator:
            try:
                self.display_emulator.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up display emulator: {e}")
        
        # Cleanup GPIO if enabled
        if self.enable_gpio:
            self.button_controller.cleanup()
        
        # Stop KitchenRadio if we own it
        if self._owns_kitchen_radio:
            try:
                self.kitchen_radio.stop()
            except Exception as e:
                logger.warning(f"Error stopping KitchenRadio: {e}")
        
        # Note: Flask development server doesn't have a clean shutdown method
        # In production, you'd use a proper WSGI server like Gunicorn
        
        logger.info("KitchenRadio Web API stopped")
    
    def press_button_direct(self, button_name: str) -> bool:
        """
        Directly press a button (bypass API).
        
        Args:
            button_name: Name of button to press
            
        Returns:
            True if successful
        """
        return self.button_controller.press_button(button_name)


# Example usage and testing
if __name__ == "__main__":
    import sys
    import os
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create KitchenRadio Web API
    api = KitchenRadioWeb(
        kitchen_radio=None,  # Will create its own
        host='127.0.0.1',
        port=5001,
        enable_gpio=False  # Disable GPIO for testing
    )
    
    if api.start():
        print("KitchenRadio Web API started successfully")
        print("API available at: http://127.0.0.1:5001")
        print("\nAvailable endpoints:")
        print("  Button Control:")
        print("    GET  /api/buttons - List all buttons")
        print("    POST /api/button/<name> - Press a button")
        print("    GET  /api/button/<name>/info - Get button info")
        print("    GET  /api/buttons/stats - Get button statistics")
        print("    POST /api/buttons/reset-stats - Reset statistics")
        print("  Display Control:")
        print("    GET  /api/display/image - Get display image (PNG)")
        print("    GET  /api/display/ascii - Get display as ASCII art")
        print("    POST /api/display/clear - Clear display")
        print("    POST /api/display/test - Show test pattern")
        print("    GET  /api/display/stats - Get display statistics")
        print("    GET  /api/display/status - Get display status")
        print("  System:")
        print("    GET  /api/status - Get API and radio status")
        print("    GET  /api/health - Health check")
        print("\nPress Ctrl+C to stop")
        
        try:
            # Keep running
            while api.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            api.stop()
    else:
        print("Failed to start KitchenRadio Web API")
        sys.exit(1)
