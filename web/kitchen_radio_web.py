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

# Add project root to path if not already there
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

# Import the main daemon
from kitchen_radio import KitchenRadio

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
            return render_template('index.html')
        
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
        
        @self.app.route('/api/mpd/<action>', methods=['POST'])
        def api_mpd_control(action):
            """Control MPD backend"""
            daemon = self._get_daemon()
            if not daemon or not daemon.mpd_connected:
                return jsonify({'error': 'MPD not connected'}), 400
            
            try:
                controller = daemon.mpd_controller
                
                if action == 'play':
                    result = controller.play()
                elif action == 'pause':
                    result = controller.pause()
                elif action == 'stop':
                    result = controller.stop() if hasattr(controller, 'stop') else False
                elif action == 'next':
                    result = controller.next_track()
                elif action == 'previous':
                    result = controller.previous_track()
                elif action == 'volume':
                    data = request.get_json()
                    if not data or 'level' not in data:
                        return jsonify({'error': 'Volume level required'}), 400
                    level = int(data['level'])
                    if 0 <= level <= 100:
                        result = controller.set_volume(level)
                    else:
                        return jsonify({'error': 'Volume must be 0-100'}), 400
                else:
                    return jsonify({'error': f'Unknown action: {action}'}), 400
                
                return jsonify({'success': result})
                
            except Exception as e:
                logger.error(f"Error controlling MPD: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/librespot/<action>', methods=['POST'])
        def api_librespot_control(action):
            """Control librespot backend"""
            daemon = self._get_daemon()
            if not daemon or not daemon.librespot_connected:
                return jsonify({'error': 'Librespot not connected'}), 400
            
            try:
                controller = daemon.librespot_controller
                
                if action == 'play':
                    result = controller.play()
                elif action == 'pause':
                    result = controller.pause()
                elif action == 'stop':
                    result = controller.stop() if hasattr(controller, 'stop') else False
                elif action == 'next':
                    result = controller.next_track()
                elif action == 'previous':
                    result = controller.previous_track()
                elif action == 'volume':
                    data = request.get_json()
                    if not data or 'level' not in data:
                        return jsonify({'error': 'Volume level required'}), 400
                    level = int(data['level'])
                    if 0 <= level <= 100:
                        result = controller.set_volume(level)
                    else:
                        return jsonify({'error': 'Volume must be 0-100'}), 400
                else:
                    return jsonify({'error': f'Unknown action: {action}'}), 400
                
                return jsonify({'success': result})
                
            except Exception as e:
                logger.error(f"Error controlling librespot: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/volume/<backend>/<action>', methods=['POST'])
        def api_volume_control(backend, action):
            """Quick volume control"""
            daemon = self._get_daemon()
            if not daemon:
                return jsonify({'error': 'Daemon not available'}), 400
            
            try:
                if backend == 'mpd' and daemon.mpd_connected:
                    controller = daemon.mpd_controller
                    monitor = daemon.mpd_monitor
                elif backend == 'librespot' and daemon.librespot_connected:
                    controller = daemon.librespot_controller
                    monitor = daemon.librespot_monitor
                else:
                    return jsonify({'error': f'{backend} not connected'}), 400
                
                current_volume = monitor.get_volume()
                if current_volume is None:
                    return jsonify({'error': 'Unable to get current volume'}), 500
                
                if action == 'up':
                    new_volume = min(100, current_volume + 5)
                elif action == 'down':
                    new_volume = max(0, current_volume - 5)
                else:
                    return jsonify({'error': f'Unknown volume action: {action}'}), 400
                
                result = controller.set_volume(new_volume)
                return jsonify({'success': result, 'volume': new_volume})
                
            except Exception as e:
                logger.error(f"Error controlling volume: {e}")
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
