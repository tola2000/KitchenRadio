#!/usr/bin/env python3
"""
KitchenRadio Flask Debug Setup
"""

import os
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "web"))

# Set Flask environment variables for debugging
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'
os.environ['FLASK_APP'] = 'kitchen_radio_web.py'

# Set debug mode for KitchenRadio
os.environ['DEBUG'] = 'true'
os.environ['LOG_LEVEL'] = 'DEBUG'

# Import and run the web server
from web.kitchen_radio_web import KitchenRadioWebServer

if __name__ == "__main__":
    print("🐛 Starting KitchenRadio Web Interface in DEBUG mode")
    print("=" * 50)
    print("📍 Web interface will be available at: http://localhost:5000")
    print("🔧 Flask debug mode: ENABLED")
    print("🔍 Auto-reload on file changes: ENABLED")
    print("📊 Detailed error pages: ENABLED")
    print("📝 Debug logging: ENABLED")
    print("=" * 50)
    print()
    
    # Create and run web server in debug mode
    server = KitchenRadioWebServer(host='127.0.0.1', port=5000, debug=True)
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n👋 Debug session ended")
    except Exception as e:
        print(f"\n❌ Debug session error: {e}")
        sys.exit(1)
