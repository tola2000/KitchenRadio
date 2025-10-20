"""
KitchenRadio Radio Package

This package contains the main KitchenRadio functionality and hardware controllers:
- Main KitchenRadio daemon class
- Hardware controllers for physical radio interfaces (GPIO buttons, I2C displays)
- Backend integration and unified control
"""

# Import main radio functionality
from .kitchen_radio import KitchenRadio, BackendType

# Try to import hardware controllers if available
try:
    from .hardware.button_controller import ButtonController
    from .hardware.display_controller import DisplayController  
    from .hardware.hardware_integration import HardwareIntegration
    HARDWARE_CONTROLLERS_AVAILABLE = True
except ImportError:
    # Hardware controllers not available (missing dependencies or not on Raspberry Pi)
    ButtonController = None
    DisplayController = None
    HardwareIntegration = None
    HARDWARE_CONTROLLERS_AVAILABLE = False

# Import hardware configuration utilities
from .hardware_config import HardwareConfig, setup_hardware_environment

__version__ = "1.0.0"
__author__ = "KitchenRadio Team"

# Main exports
__all__ = [
    'KitchenRadio',
    'BackendType',
    'HARDWARE_CONTROLLERS_AVAILABLE',
    'HardwareConfig',
    'setup_hardware_environment'
]

# Add hardware exports if available
if HARDWARE_CONTROLLERS_AVAILABLE:
    __all__.extend(['ButtonController', 'DisplayController', 'HardwareIntegration'])

# Hardware availability flags
HARDWARE_AVAILABLE = {
    'gpio': False,
    'i2c': False,
    'display': False
}

def check_hardware_availability():
    """
    Check what hardware interfaces are available on this system.
    
    Returns:
        dict: Dictionary with availability flags for different hardware components
    """
    global HARDWARE_AVAILABLE
    
    # Check for RPi.GPIO
    try:
        import RPi.GPIO as GPIO
        HARDWARE_AVAILABLE['gpio'] = True
    except ImportError:
        HARDWARE_AVAILABLE['gpio'] = False
    
    # Check for I2C libraries
    try:
        import smbus2
        import board
        import busio
        HARDWARE_AVAILABLE['i2c'] = True
    except ImportError:
        HARDWARE_AVAILABLE['i2c'] = False
    
    # Check for display libraries
    try:
        import adafruit_ssd1306
        from PIL import Image, ImageDraw, ImageFont
        HARDWARE_AVAILABLE['display'] = True
    except ImportError:
        HARDWARE_AVAILABLE['display'] = False
    
    return HARDWARE_AVAILABLE.copy()

def get_hardware_info():
    """
    Get information about available hardware interfaces.
    
    Returns:
        dict: Hardware information and availability
    """
    availability = check_hardware_availability()
    
    info = {
        'platform': 'unknown',
        'gpio_available': availability['gpio'],
        'i2c_available': availability['i2c'],
        'display_available': availability['display'],
        'simulation_mode': not (availability['gpio'] and availability['i2c']),
        'supported_displays': [],
        'supported_buttons': []
    }
    
    # Detect platform
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi' in cpuinfo:
                info['platform'] = 'raspberry_pi'
            elif 'BCM' in cpuinfo:
                info['platform'] = 'broadcom'
    except:
        info['platform'] = 'generic'
    
    # List supported displays
    if availability['display']:
        info['supported_displays'] = [
            'SSD1306 128x64 OLED',
            'SSD1306 128x32 OLED', 
            'SH1106 128x64 OLED'
        ]
    
    # List supported button configurations
    if availability['gpio']:
        info['supported_buttons'] = [
            'Standard KitchenRadio Layout (12 buttons)',
            'Minimal Layout (6 buttons)',
            'Custom GPIO Mapping'
        ]
    
    return info

def create_hardware_controllers(config=None):
    """
    Factory function to create hardware controllers based on system capabilities.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        tuple: (button_controller, display_controller, hardware_integration)
    """
    if config is None:
        config = {}
    
    availability = check_hardware_availability()
    
    # Create button controller
    button_controller = ButtonController(
        simulation_mode=not availability['gpio'],
        **config.get('buttons', {})
    )
    
    # Create display controller  
    display_controller = DisplayController(
        simulation_mode=not availability['display'],
        **config.get('display', {})
    )
    
    # Create hardware integration
    hardware_integration = HardwareIntegration(
        button_controller=button_controller,
        display_controller=display_controller,
        **config.get('integration', {})
    )
    
    return button_controller, display_controller, hardware_integration

# Auto-check hardware on import
check_hardware_availability()
