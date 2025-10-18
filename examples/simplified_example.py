#!/usr/bin/env python3
"""
Example showing simplified import with multiple path configuration
"""

# With the updated .env configuration, you only need this single import
# It will automatically add both project root and src to Python path
import env_config

# Now you can import both:
import project_config  # From project root
from kitchenradio.mpd import KitchenRadioClient, PlaybackController  # From src


def main():
    print("🎵 KitchenRadio - Simplified Multiple Path Example")
    
    # Get configuration
    config = env_config.get_config()
    config.print_config()
    
    # Get MPD defaults using project_config helper
    mpd_defaults = project_config.get_mpd_defaults()
    print(f"\n🔌 MPD defaults: {mpd_defaults}")
    
    try:
        # Create client using configuration
        client = KitchenRadioClient(
            host=config.mpd_host,
            port=config.mpd_port,
            password=config.mpd_password,
            timeout=config.mpd_timeout
        )
        
        print(f"\n🔌 Connecting to MPD at {config.mpd_host}:{config.mpd_port}")
        
        # Connect
        if not client.connect():
            print("❌ Connection failed")
            return 1
        
        print("✅ Connected successfully!")
        
        # Create controller
        controller = PlaybackController(client)
        
        # Show status
        status = controller.get_status()
        print(f"📊 Status: {status.get('state', 'unknown')}")
        
        volume = controller.get_volume()
        print(f"🔊 Volume: {volume}%")
        
        print("\n💡 Both project_config.py and kitchenradio.mpd are accessible!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        if 'client' in locals():
            client.disconnect()


if __name__ == "__main__":
    import sys
    sys.exit(main())
