#!/usr/bin/env python3
"""
KitchenRadio Web Interface - Flask-based web UI
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, Any

from flask import Flask, render_template, jsonify, request, send_static_file
from flask_cors import CORS

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
        
        # Create Flask app
        self.app = Flask(__name__, 
                        template_folder='web/templates',
                        static_folder='web/static')
        
        # Enable CORS for API endpoints
        CORS(self.app, resources={r"/api/*": {"origins": "*"}})
        
        # Configure logging
        if not debug:
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.WARNING)
        
        self._setup_routes()
        
        logger.info(f"KitchenRadio web server initialized on {host}:{port}")
    
    def _get_daemon(self):
        """Get or create daemon instance"""
        if not self.daemon:
            self.daemon = KitchenRadio()
            if not self.daemon.start():
                logger.error("Failed to start KitchenRadio daemon")
                return None
        return self.daemon
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main interface page"""
            return render_template('index.html')
        
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
        try:
            self.app.run(host=self.host, port=self.port, debug=self.debug, threaded=True)
        except Exception as e:
            logger.error(f"Web server error: {e}")
        finally:
            if self.daemon:
                self.daemon.stop()


def main():
    """Main entry point for web server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KitchenRadio Web Interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
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
