#!/usr/bin/env python3
"""
Template for using Method 3 (Project Config) in KitchenRadio scripts

Copy this template for new scripts that need to import kitchenradio.mpd modules.
"""

import sys
from pathlib import Path

# ===== METHOD 3: PROJECT CONFIG SETUP =====
# Add this block to the top of any script that needs to import kitchenradio.mpd
sys.path.insert(0, str(Path(__file__).parent.parent))
import project_config  # This automatically configures the Python path
# ==========================================

# Now you can import normally
from kitchenradio.mpd import KitchenRadioClient, PlaybackController, NowPlayingMonitor


def main():
    """
    Your main function here.
    """
    print("🎵 KitchenRadio Script Template")
    
    # Example usage:
    try:
        # Create client
        client = KitchenRadioClient(host="localhost", port=6600)
        
        # Connect
        if not client.connect():
            print("❌ Connection failed")
            return 1
        
        print("✅ Connected to MPD")
        
        # Your code here...
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        # Always disconnect
        if 'client' in locals():
            client.disconnect()


if __name__ == "__main__":
    sys.exit(main())
