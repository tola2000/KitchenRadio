#!/usr/bin/env python3
"""
Method 3: Using Project Config Module for Path Setup
"""

import sys
from pathlib import Path

# Add project root to path to access project_config
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import project config - this automatically sets up the Python path
import project_config

# Now you can import normally without any path manipulation
from kitchenradio.mpd import KitchenRadioClient, PlaybackController, NowPlayingMonitor


def main():
    print("🎵 KitchenRadio - Method 3: Project Config")
    print(f"📁 Project root: {project_config.get_project_root()}")
    print(f"📁 Source path: {project_config.get_src_path()}")
    
    try:
        # Test imports
        print("✅ Testing imports...")
        
        # Create client
        client = KitchenRadioClient(host="localhost", port=6600)
        print("✅ KitchenRadioClient imported successfully")
        
        # Create controller
        controller = PlaybackController(client)
        print("✅ PlaybackController imported successfully")
        
        # Create monitor
        monitor = NowPlayingMonitor(client)
        print("✅ NowPlayingMonitor imported successfully")
        
        print("\n🎉 All imports successful using Method 3!")
        print("💡 You can now use this pattern in any script:")
        print("   import project_config")
        print("   from kitchenradio.mpd import KitchenRadioClient")
        
        return 0
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
