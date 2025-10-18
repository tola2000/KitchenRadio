"""
Project configuration and path setup for KitchenRadio

This module now uses .env configuration for flexible path setup.
"""

import sys
from pathlib import Path

# Import the new env_config module
from env_config import get_config

def setup_project_path():
    """Add the src directory to Python path if not already there."""
    config = get_config()
    src_path = config.get_src_path()
    
    if src_path and src_path.exists():
        str_path = str(src_path)
        if str_path not in sys.path:
            sys.path.insert(0, str_path)
            print(f"✅ Added {str_path} to Python path")
        return src_path
    else:
        print(f"⚠️ Source path not found: {src_path}")
        return None

def get_project_root():
    """Get the project root directory."""
    return get_config().project_root

def get_src_path():
    """Get the src directory path."""
    return get_config().get_src_path()

def get_mpd_defaults():
    """Get default MPD connection settings from .env."""
    config = get_config()
    return {
        'host': config.mpd_host,
        'port': config.mpd_port,
        'password': config.mpd_password,
        'timeout': config.mpd_timeout
    }

# Auto-setup when imported
setup_project_path()
