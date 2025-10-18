"""
Project configuration and path setup for KitchenRadio
"""

import sys
from pathlib import Path

def setup_project_path():
    """Add the src directory to Python path if not already there."""
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print(f"✅ Added {src_path} to Python path")
    
    return src_path

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent

def get_src_path():
    """Get the src directory path."""
    return get_project_root() / "src"

# Auto-setup when imported
setup_project_path()
