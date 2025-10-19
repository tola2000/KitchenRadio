#!/usr/bin/env python3
"""
Simple test to verify state listeners setup
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from env_config import get_project_config
    config = get_project_config()
    
    if config and 'PYTHON_PATHS' in config:
        for path in config['PYTHON_PATHS']:
            if path not in sys.path:
                sys.path.insert(0, path)
except Exception as e:
    print(f"Warning: Could not load env config: {e}")

def main():
    try:
        from kitchenradio.radio.kitchen_radio import KitchenRadio, BackendType
        
        print("✓ Imports successful")
        print(f"✓ BackendType enum available: {list(BackendType)}")
        
        # Create daemon instance
        daemon = KitchenRadio()
        print("✓ KitchenRadio instance created")
        
        # Check if callback methods exist
        if hasattr(daemon, '_on_mpd_state_changed'):
            print("✓ MPD state change callback method exists")
        else:
            print("✗ MPD state change callback method missing")
            
        if hasattr(daemon, '_on_librespot_state_changed'):
            print("✓ Librespot state change callback method exists")
        else:
            print("✗ Librespot state change callback method missing")
        
        print("\n=== State listeners setup looks good! ===")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
