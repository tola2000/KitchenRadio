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
try:
    from web.kitchen_radio_web import KitchenRadioWebServer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n💡 Troubleshooting steps:")
    print("1. Make sure you're in the KitchenRadio project root directory")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Check that the web/ directory exists with kitchen_radio_web.py")
    print("4. Verify Python path includes project directories")
    sys.exit(1)

if __name__ == "__main__":
    print("🐛 Starting KitchenRadio Web Interface in DEBUG mode")
    print("=" * 60)
    print("📍 Web interface will be available at: http://localhost:5000")
    print("🎵 KitchenRadio daemon will start automatically")
    print("🔧 Flask debug mode: ENABLED")
    print("🔍 Auto-reload on file changes: ENABLED")
    print("📊 Detailed error pages: ENABLED")
    print("📝 Debug logging: ENABLED")
    print("=" * 60)
    print("📋 Available endpoints:")
    print("   🏠 http://localhost:5000/           - Web interface")
    print("   🔍 http://localhost:5000/api/health - Health check")
    print("   📊 http://localhost:5000/api/status - Backend status")
    print("=" * 60)
    print()
    
    try:
        # Create and run web server in debug mode
        server = KitchenRadioWebServer(host='127.0.0.1', port=5000, debug=True)
        server.run()
    except KeyboardInterrupt:
        print("\n👋 Debug session ended")
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("💡 Try: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Debug session error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
