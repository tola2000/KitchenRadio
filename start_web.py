#!/usr/bin/env python3
"""
KitchenRadio Web + Daemon Startup Script
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def main():
    print("🎵 KitchenRadio Web + Daemon Launcher")
    print("=" * 45)
    
    try:
        from web.kitchen_radio_web import KitchenRadioWebServer
        
        print("✅ Web server module loaded")
        
        # Create web server (this will automatically start the daemon)
        print("🚀 Starting integrated web server + daemon...")
        server = KitchenRadioWebServer(host='0.0.0.0', port=5000, debug=False)
        
        print("📋 Service Details:")
        print(f"   🌐 Web Interface: http://0.0.0.0:5000")
        print(f"   🎛️  Control Panel: http://0.0.0.0:5000")
        print(f"   🔍 Health Check: http://0.0.0.0:5000/api/health")
        print(f"   📊 Status API: http://0.0.0.0:5000/api/status")
        print()
        print("🎵 The KitchenRadio daemon will start automatically")
        print("🔌 Both MPD and Spotify (librespot) backends will be monitored")
        print("🔍 Press Ctrl+C to stop everything")
        print("=" * 45)
        
        # Run the server (includes daemon)
        server.run()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure Flask is installed: pip install -r requirements.txt")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
