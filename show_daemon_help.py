#!/usr/bin/env python3
"""
Test script to show run_daemon.py help without importing dependencies
"""

import sys
import argparse

def show_help():
    parser = argparse.ArgumentParser(
        description='KitchenRadio Daemon - Multi-source audio controller',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with hardware controls only (default)
  python run_daemon.py
  
  # Run with web interface on port 8080
  python run_daemon.py --web --port 8080
  
  # Run with web interface, no hardware
  python run_daemon.py --web --no-hardware
  
  # Run web only (no display, no buttons)
  python run_daemon.py --web --no-display --no-buttons
  
  # Custom web host and port
  python run_daemon.py --web --host 0.0.0.0 --port 5000
        """
    )
    
    # Web interface options
    parser.add_argument('--web', action='store_true',
                        help='Enable web interface')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Web server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Web server port (default: 5000)')
    
    # Hardware control options
    parser.add_argument('--no-hardware', action='store_true',
                        help='Disable all hardware (display + buttons)')
    parser.add_argument('--no-display', action='store_true',
                        help='Disable display controller')
    parser.add_argument('--no-buttons', action='store_true',
                        help='Disable button controller')
    
    # Logging options
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    parser.print_help()

if __name__ == "__main__":
    show_help()
