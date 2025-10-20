"""
Hardware Configuration for KitchenRadio Physical Interface

This file contains configuration examples and helper functions for setting up
the physical radio hardware on Raspberry Pi.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class HardwareConfig:
    """Configuration manager for KitchenRadio hardware"""
    
    # Default hardware configuration
    DEFAULT_CONFIG = {
        'buttons': {
            'enabled': True,
            'debounce_time': 0.1,
            'pin_mapping': {
                # Source buttons (top row)
                'source_mpd': 2,
                'source_spotify': 3,
                
                # Menu buttons (around display)
                'menu_up': 17,
                'menu_menu': 27,
                'menu_down': 22,
                'menu_set': 10,
                'menu_ok': 9,
                'menu_exit': 11,
                
                # Transport controls (middle row)
                'transport_prev': 5,
                'transport_play': 6,
                'transport_stop': 13,
                'transport_next': 19,
                
                # Volume controls (bottom left/right)
                'volume_down': 26,
                'volume_up': 21,
                
                # Power button (bottom center)
                'power': 4
            }
        },
        'display': {
            'enabled': True,
            'type': 'ssd1306',
            'width': 128,
            'height': 64,
            'i2c_address': 0x3C,
            'i2c_bus': 1,
            'reset_pin': None,
            'rotation': 0,
            'font_size': 8,
            'scroll_speed': 2,
            'update_interval': 0.1
        },
        'integration': {
            'enabled': True,
            'auto_start': True,
            'web_integration': True,
            'status_led_pin': None,
            'power_button_pin': None
        }
    }
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize hardware configuration.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file and config_file.exists():
            self.load_config(config_file)
    
    def load_config(self, config_file: Path):
        """
        Load configuration from file.
        
        Args:
            config_file: Path to configuration file
        """
        try:
            import json
            with open(config_file, 'r') as f:
                user_config = json.load(f)
            
            # Merge with default config
            self._merge_config(self.config, user_config)
            logger.info(f"Loaded hardware configuration from {config_file}")
            
        except Exception as e:
            logger.error(f"Error loading config from {config_file}: {e}")
    
    def save_config(self, config_file: Path):
        """
        Save current configuration to file.
        
        Args:
            config_file: Path to save configuration to
        """
        try:
            import json
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved hardware configuration to {config_file}")
            
        except Exception as e:
            logger.error(f"Error saving config to {config_file}: {e}")
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]):
        """
        Recursively merge configuration dictionaries.
        
        Args:
            base: Base configuration dictionary
            update: Update configuration dictionary
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get_button_config(self) -> Dict[str, Any]:
        """Get button controller configuration"""
        return self.config['buttons']
    
    def get_display_config(self) -> Dict[str, Any]:
        """Get display controller configuration"""
        return self.config['display']
    
    def get_integration_config(self) -> Dict[str, Any]:
        """Get hardware integration configuration"""
        return self.config['integration']
    
    def is_hardware_enabled(self) -> bool:
        """Check if hardware controllers are enabled"""
        return (self.config['buttons']['enabled'] or 
                self.config['display']['enabled'] or
                self.config['integration']['enabled'])


def create_default_config_file(config_path: Path):
    """
    Create a default hardware configuration file.
    
    Args:
        config_path: Path where to create the config file
    """
    config = HardwareConfig()
    config.save_config(config_path)
    
    logger.info(f"Created default hardware configuration at {config_path}")
    print(f"Default hardware configuration created at: {config_path}")
    print("\nTo customize your hardware setup:")
    print("1. Edit the pin mappings in the 'buttons' section")
    print("2. Configure your display settings in the 'display' section")
    print("3. Set integration options in the 'integration' section")


def get_raspberry_pi_info():
    """
    Get information about the current Raspberry Pi hardware.
    
    Returns:
        Dict with Raspberry Pi information or None if not on RPi
    """
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        info = {
            'is_raspberry_pi': False,
            'model': 'Unknown',
            'revision': 'Unknown',
            'gpio_pins': 0
        }
        
        if 'Raspberry Pi' in cpuinfo:
            info['is_raspberry_pi'] = True
            
            # Extract model information
            for line in cpuinfo.split('\n'):
                if line.startswith('Model'):
                    info['model'] = line.split(':', 1)[1].strip()
                elif line.startswith('Revision'):
                    info['revision'] = line.split(':', 1)[1].strip()
            
            # Determine GPIO pin count based on model
            if any(model in info['model'] for model in ['Pi 4', 'Pi 3', 'Pi 2', 'Pi Zero']):
                info['gpio_pins'] = 40
            elif 'Pi 1' in info['model']:
                info['gpio_pins'] = 26
        
        return info
        
    except Exception as e:
        logger.debug(f"Could not get Raspberry Pi info: {e}")
        return None


def check_i2c_devices():
    """
    Check for available I2C devices.
    
    Returns:
        List of detected I2C device addresses
    """
    devices = []
    
    try:
        import smbus2
        
        # Check common I2C buses
        for bus_num in [0, 1]:
            try:
                bus = smbus2.SMBus(bus_num)
                
                # Scan for devices
                for addr in range(0x03, 0x78):
                    try:
                        bus.read_byte(addr)
                        devices.append({
                            'bus': bus_num,
                            'address': f'0x{addr:02X}',
                            'decimal': addr
                        })
                    except:
                        pass
                
                bus.close()
                
            except Exception as e:
                logger.debug(f"Could not scan I2C bus {bus_num}: {e}")
    
    except ImportError:
        logger.warning("smbus2 not available for I2C scanning")
    
    return devices


def setup_hardware_environment():
    """
    Set up the environment for hardware operation.
    
    Returns:
        Dict with setup status and information
    """
    status = {
        'raspberry_pi': False,
        'gpio_available': False,
        'i2c_available': False,
        'display_libraries': False,
        'i2c_devices': [],
        'recommendations': []
    }
    
    # Check Raspberry Pi
    pi_info = get_raspberry_pi_info()
    if pi_info and pi_info['is_raspberry_pi']:
        status['raspberry_pi'] = True
        logger.info(f"Running on {pi_info['model']}")
    else:
        status['recommendations'].append("Hardware controllers require Raspberry Pi")
    
    # Check GPIO
    try:
        import RPi.GPIO as GPIO
        status['gpio_available'] = True
        logger.info("RPi.GPIO available")
    except ImportError:
        status['recommendations'].append("Install RPi.GPIO: pip install RPi.GPIO")
    
    # Check I2C
    try:
        import smbus2
        status['i2c_available'] = True
        status['i2c_devices'] = check_i2c_devices()
        logger.info(f"I2C available, found {len(status['i2c_devices'])} devices")
    except ImportError:
        status['recommendations'].append("Install smbus2: pip install smbus2")
    
    # Check display libraries
    try:
        import adafruit_ssd1306
        from PIL import Image, ImageDraw, ImageFont
        status['display_libraries'] = True
        logger.info("Display libraries available")
    except ImportError:
        status['recommendations'].append("Install display libraries: pip install adafruit-circuitpython-ssd1306 Pillow")
    
    return status


if __name__ == "__main__":
    # Command-line utility for hardware setup
    import argparse
    
    parser = argparse.ArgumentParser(description='KitchenRadio Hardware Configuration')
    parser.add_argument('--create-config', metavar='PATH', help='Create default config file')
    parser.add_argument('--check-hardware', action='store_true', help='Check hardware availability')
    parser.add_argument('--scan-i2c', action='store_true', help='Scan for I2C devices')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_default_config_file(Path(args.create_config))
    
    if args.check_hardware:
        status = setup_hardware_environment()
        print("\nHardware Status:")
        print(f"  Raspberry Pi: {'✓' if status['raspberry_pi'] else '✗'}")
        print(f"  GPIO: {'✓' if status['gpio_available'] else '✗'}")
        print(f"  I2C: {'✓' if status['i2c_available'] else '✗'}")
        print(f"  Display Libraries: {'✓' if status['display_libraries'] else '✗'}")
        
        if status['recommendations']:
            print("\nRecommendations:")
            for rec in status['recommendations']:
                print(f"  • {rec}")
    
    if args.scan_i2c:
        devices = check_i2c_devices()
        print(f"\nFound {len(devices)} I2C devices:")
        for device in devices:
            print(f"  Bus {device['bus']}: {device['address']} ({device['decimal']})")
