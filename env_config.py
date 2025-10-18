"""
Environment configuration loader for KitchenRadio

This module loads configuration from .env file and environment variables.
"""

import os
import sys
from pathlib import Path
from typing import Optional


class Config:
    """Configuration class that loads from .env file and environment variables."""
    
    def __init__(self):
        """Initialize configuration by loading .env file."""
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / '.env'
        self._load_env_file()
        self._setup_python_path()
    
    def _load_env_file(self):
        """Load environment variables from .env file."""
        if not self.env_file.exists():
            print(f"⚠️ .env file not found at {self.env_file}")
            return
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line.startswith('#') or not line or '=' not in line:
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Expand environment variables in value
                    value = os.path.expandvars(value)
                    
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value
                        
        except Exception as e:
            print(f"❌ Error loading .env file: {e}")
    
    def _setup_python_path(self):
        """Set up Python path based on configuration."""
        src_path = self.get_src_path()
        
        if src_path and src_path.exists():
            str_path = str(src_path)
            if str_path not in sys.path:
                sys.path.insert(0, str_path)
                print(f"✅ Added {str_path} to Python path")
        else:
            print(f"⚠️ Source path not found: {src_path}")
    
    def get_src_path(self) -> Optional[Path]:
        """Get the source directory path."""
        src_relative = os.getenv('KITCHENRADIO_SRC_PATH', 'src')
        
        if os.path.isabs(src_relative):
            return Path(src_relative)
        else:
            return self.project_root / src_relative
    
    @property
    def mpd_host(self) -> str:
        """Get MPD host."""
        return os.getenv('MPD_HOST', 'localhost')
    
    @property
    def mpd_port(self) -> int:
        """Get MPD port."""
        return int(os.getenv('MPD_PORT', '6600'))
    
    @property
    def mpd_password(self) -> Optional[str]:
        """Get MPD password."""
        password = os.getenv('MPD_PASSWORD', '')
        return password if password else None
    
    @property
    def mpd_timeout(self) -> int:
        """Get MPD timeout."""
        return int(os.getenv('MPD_TIMEOUT', '10'))
    
    @property
    def default_volume(self) -> int:
        """Get default volume."""
        return int(os.getenv('DEFAULT_VOLUME', '50'))
    
    @property
    def log_level(self) -> str:
        """Get log level."""
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    @property
    def debug(self) -> bool:
        """Get debug mode flag."""
        return os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes', 'on')
    
    @property
    def dev_mode(self) -> bool:
        """Get development mode flag."""
        return os.getenv('DEV_MODE', 'false').lower() in ('true', '1', 'yes', 'on')
    
    def print_config(self):
        """Print current configuration."""
        print("🔧 KitchenRadio Configuration:")
        print(f"  📁 Project root: {self.project_root}")
        print(f"  📁 Source path: {self.get_src_path()}")
        print(f"  🎵 MPD host: {self.mpd_host}")
        print(f"  🎵 MPD port: {self.mpd_port}")
        print(f"  🎵 MPD timeout: {self.mpd_timeout}s")
        print(f"  🔊 Default volume: {self.default_volume}%")
        print(f"  📝 Log level: {self.log_level}")
        print(f"  🐛 Debug mode: {self.debug}")
        print(f"  🔧 Dev mode: {self.dev_mode}")


# Global configuration instance
config = Config()

# Convenience functions
def get_config() -> Config:
    """Get the global configuration instance."""
    return config

def setup_logging():
    """Set up logging based on configuration."""
    import logging
    
    level = getattr(logging, config.log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    if config.debug:
        logging.getLogger().setLevel(logging.DEBUG)


# Auto-setup when imported
if __name__ != '__main__':
    # Only auto-setup when imported, not when run directly
    pass
else:
    # When run directly, print configuration
    config.print_config()
