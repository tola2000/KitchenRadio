#!/usr/bin/env python3
"""
Install script for development setup
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Install KitchenRadio in development mode."""
    print("🔧 Installing KitchenRadio in development mode...")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    try:
        # Install in editable/development mode
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", str(project_root)
        ], check=True, capture_output=True, text=True)
        
        print("✅ Installation successful!")
        print("Now you can import with: from kitchenradio.mpd import KitchenRadioClient")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print(f"Error output: {e.stderr}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
