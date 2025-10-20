#!/usr/bin/env python3
"""
KitchenRadio Web Interface - Flask-based web UI
"""

import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import Dict, Any

from flask import Flask, render_template, jsonify, request

try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("Warning: Flask-CORS not available. Install with: pip install Flask-CORS")

# # Add project root to path if not already there
# project_root = Path(__file__).parent.parent
# if str(project_root) not in sys.path:
#     sys.path.insert(0, str(project_root))
# if str(project_root / "src") not in sys.path:
#     sys.path.insert(0, str(project_root / "src"))

# Import the main daemon
from kitchenradio.radio.kitchen_radio import KitchenRadio

logger = logging.getLogger(__name__)


class KitchenRadioWebServer:
    """Web interface for KitchenRadio daemon"""
    
    def __init__(self, host='0.0.0.0', port=5000, debug=False):
        """
        Initialize web server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        self.host = host
        self.port = port
        self.debug = debug
        self.daemon = None
        self.daemon_started = False
        
        # Create Flask app with absolute paths
        web_dir = Path(__file__).parent
        self.app = Flask(__name__, 
                        template_folder=str(web_dir / 'templates'),
                        static_folder=str(web_dir / 'static'))
        
        # Enable CORS for API endpoints if available
        if CORS_AVAILABLE:
            CORS(self.app, resources={r"/api/*": {"origins": "*"}})
        else:
            # Manual CORS headers for API routes
            @self.app.after_request
            def after_request(response):
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,PATCH,OPTIONS')
                return response
        
        # Configure logging
        if not debug:
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.WARNING)
        
        self._setup_routes()
        
        logger.info(f"KitchenRadio web server initialized on {host}:{port}")
    
    def _start_daemon(self):
        """Start the KitchenRadio daemon"""
        if self.daemon_started:
            return True
            
        logger.info("Starting KitchenRadio daemon...")
        try:
            self.daemon = KitchenRadio()
            if self.daemon.start():
                self.daemon_started = True
                logger.info("✅ KitchenRadio daemon started successfully")
                return True
            else:
                logger.error("❌ Failed to start KitchenRadio daemon")
                return False
        except Exception as e:
            logger.error(f"❌ Error starting KitchenRadio daemon: {e}")
            return False
    
    def _stop_daemon(self):
        """Stop the KitchenRadio daemon"""
        if self.daemon and self.daemon_started:
            logger.info("Stopping KitchenRadio daemon...")
            try:
                self.daemon.stop()
                self.daemon_started = False
                logger.info("✅ KitchenRadio daemon stopped")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping daemon: {e}")
    
    def _get_daemon(self):
        """Get or create daemon instance"""
        if not self.daemon_started:
            if not self._start_daemon():
                return None
        return self.daemon
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main interface page"""
            return render_template('unified_control.html')
        
        @self.app.route('/api/health')
        def api_health():
            """Health check endpoint"""
            daemon_status = "running" if self.daemon_started and self.daemon else "stopped"
            return jsonify({
                'web_server': 'running',
                'daemon': daemon_status,
                'timestamp': time.time()
            })
        
        @self.app.route('/api/status')
        def api_status():
            """Get current status of both backends"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'error': 'Failed to connect to daemon'}), 500
            
            try:

                status = daemon.get_status()
                return jsonify(status)
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/source')
        def api_get_source():
            """Get current audio source"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'error': 'Failed to connect to daemon'}), 500
            
            try:
                current_source = daemon.get_current_source()
                available_sources = daemon.get_available_sources()
                
                return jsonify({
                    'success': True,
                    'current_source': current_source.value if current_source else None,
                    'available_sources': [s.value for s in available_sources]
                })
            except Exception as e:
                logger.error(f"Error getting source: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/source/<source_name>', methods=['POST'])
        def api_set_source(source_name):
            """Set audio source"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'error': 'Failed to connect to daemon'}), 500
            
            # Import here to avoid circular imports
            from kitchenradio.radio.kitchen_radio import BackendType
            
            try:
                # Validate source name
                if source_name.lower() == 'mpd':
                    source = BackendType.MPD
                elif source_name.lower() == 'spotify' or source_name.lower() == 'librespot':
                    source = BackendType.LIBRESPOT
                else:
                    return jsonify({
                        'success': False, 
                        'error': f'Invalid source: {source_name}. Valid sources: mpd, spotify'
                    }), 400
                
                # Set the source
                success = daemon.set_source(source)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Source set to {source.value}',
                        'current_source': source.value
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to set source to {source.value}'
                    }), 400
                    
            except Exception as e:
                logger.error(f"Error setting source: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/control/<action>', methods=['POST'])
        def api_active_source_control(action):
            """Control playback on the currently active source"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'error': 'Failed to connect to daemon'}), 500
            
            # Check if there's an active source
            current_source = daemon.get_current_source()
            if not current_source:
                return jsonify({
                    'success': False,
                    'error': 'No active source set. Please select a source first.'
                }), 400
            
            try:
                # Map actions to daemon methods
                action_map = {
                    'play': daemon.play,
                    'pause': daemon.pause,
                    'stop': daemon.stop,
                    'next': daemon.next,
                    'previous': daemon.previous,
                    'play_pause': daemon.play_pause
                }
                
                if action not in action_map:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid action: {action}. Valid actions: {list(action_map.keys())}'
                    }), 400
                
                # Execute the command
                result = action_map[action]()
                
                if result:
                    return jsonify({
                        'success': True,
                        'message': f'{action.capitalize()} command sent to {current_source.value}',
                        'current_source': current_source.value
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to execute {action} on {current_source.value}'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Error executing {action}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/volume', methods=['GET'])
        def api_get_volume():
            """Get volume from the currently active source"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'error': 'Failed to connect to daemon'}), 500
            
            current_source = daemon.get_current_source()
            if not current_source:
                return jsonify({
                    'success': False,
                    'error': 'No active source set'
                }), 400
            
            try:
                volume = daemon.get_volume()
                return jsonify({
                    'success': True,
                    'volume': volume,
                    'current_source': current_source.value
                })
            except Exception as e:
                logger.error(f"Error getting volume: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/volume/<int:level>', methods=['POST'])
        def api_set_volume(level):
            """Set volume on the currently active source"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'error': 'Failed to connect to daemon'}), 500
            
            current_source = daemon.get_current_source()
            if not current_source:
                return jsonify({
                    'success': False,
                    'error': 'No active source set'
                }), 400
            
            try:
                result = daemon.set_volume(level)
                if result:
                    return jsonify({
                        'success': True,
                        'volume': level,
                        'current_source': current_source.value,
                        'message': f'Volume set to {level}%'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to set volume to {level}%'
                    }), 500
            except Exception as e:
                logger.error(f"Error setting volume: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/volume/<action>', methods=['POST'])
        def api_volume_control_unified(action):
            """Unified volume control (up/down) on the currently active source"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'error': 'Failed to connect to daemon'}), 500
            
            current_source = daemon.get_current_source()
            if not current_source:
                return jsonify({
                    'success': False,
                    'error': 'No active source set'
                }), 400
            
            try:
                # Get step from request body or use default
                data = request.get_json() or {}
                step = data.get('step', 5)
                
                if action == 'up':
                    result = daemon.volume_up(step)
                    message = f'Volume increased by {step}%'
                elif action == 'down':
                    result = daemon.volume_down(step)
                    message = f'Volume decreased by {step}%'
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid volume action: {action}. Valid actions: up, down'
                    }), 400
                
                if result:
                    new_volume = daemon.get_volume()
                    return jsonify({
                        'success': True,
                        'volume': new_volume,
                        'current_source': current_source.value,
                        'message': message
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to {action} volume'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Error controlling volume: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/playlists')
        def api_get_playlists():
            """Get all stored playlists from the currently active source"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'success': False, 'error': 'Daemon not available'}), 500
            
            current_source = daemon.get_current_source()
            if not current_source:
                return jsonify({'success': False, 'error': 'No active source set'}), 400
            
            try:
                controller, source_name, is_connected = daemon._get_active_controller()
                
                if not controller:
                    return jsonify({'success': False, 'error': 'No active controller'}), 400
                
                if not is_connected:
                    return jsonify({'success': False, 'error': f'{source_name} not connected'}), 400
                
                playlists = controller.get_all_playlists()
                return jsonify({
                    'success': True, 
                    'playlists': playlists,
                    'source': source_name.lower()
                })
                
            except Exception as e:
                logger.error(f"Error getting playlists: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/load_playlist', methods=['POST'])
        def api_load_playlist():
            """Load and play a playlist on the currently active source"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'error': 'Daemon not available'}), 500
            
            current_source = daemon.get_current_source()
            if not current_source:
                return jsonify({'error': 'No active source set'}), 400
            
            data = request.get_json()
            if not data or 'playlist' not in data:
                return jsonify({'error': 'Playlist name required'}), 400
            
            playlist_name = data['playlist']
            
            try:
                controller, source_name, is_connected = daemon._get_active_controller()
                
                if not controller:
                    return jsonify({'error': 'No active controller'}), 400
                
                if not is_connected:
                    return jsonify({'error': f'{source_name} not connected'}), 400
                
                result = controller.play_playlist(playlist_name)
                
                if result:
                    return jsonify({
                        'success': True, 
                        'message': f'Loaded playlist: {playlist_name}',
                        'source': source_name.lower()
                    })
                else:
                    # Handle the case where the controller returns False (like Spotify)
                    if source_name.lower() == 'spotify':
                        return jsonify({
                            'success': False,
                            'error': 'Spotify playlists are managed through the Spotify app. Please use your Spotify client to select and play playlists.'
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'Failed to load playlist: {playlist_name}'
                        })
                
            except Exception as e:
                logger.error(f"Error loading playlist: {e}")
                return jsonify({'error': str(e)}), 500

    def run(self):
        """Run the web server"""
        logger.info(f"Starting KitchenRadio web server on {self.host}:{self.port}")
        
        # Start the KitchenRadio daemon first
        if not self._start_daemon():
            logger.error("Cannot start web server without KitchenRadio daemon")
            return
        
        try:
            logger.info(f"🌐 Web interface available at: http://{self.host}:{self.port}")
            logger.info("🎵 KitchenRadio daemon is running in background")
            logger.info("🔍 Press Ctrl+C to stop both web server and daemon")
            
            self.app.run(host=self.host, port=self.port, debug=self.debug, threaded=True)
            
        except KeyboardInterrupt:
            logger.info("🛑 Received keyboard interrupt")
        except Exception as e:
            logger.error(f"❌ Web server error: {e}")
        finally:
            logger.info("🔌 Shutting down web server and daemon...")
            self._stop_daemon()


def main():
    """Main entry point for web server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KitchenRadio Web Interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5100, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run web server
    server = KitchenRadioWebServer(host=args.host, port=args.port, debug=args.debug)
    server.run()


if __name__ == "__main__":
    main()
