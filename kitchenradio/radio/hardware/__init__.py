"""
KitchenRadio Hardware Controllers Package

Hardware interface controllers for KitchenRadio physical radio interface.
Supports both real Raspberry Pi hardware and web-based emulators.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import hardware components gracefully
try:
    from .button_controller import ButtonController, ButtonType, ButtonEvent
    from .button_controller_emulator import ButtonControllerEmulator
    BUTTON_CONTROLLER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Button controller not available: {e}")
    BUTTON_CONTROLLER_AVAILABLE = False
    ButtonController = None
    ButtonControllerEmulator = None
    ButtonType = None
    ButtonEvent = None

try:
    from .display_controller import DisplayController, DisplayType, DisplayAlignment, DisplayLine
    from .display_controller_emulator import DisplayControllerEmulator
    DISPLAY_CONTROLLER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Display controller not available: {e}")
    DISPLAY_CONTROLLER_AVAILABLE = False
    DisplayController = None
    DisplayControllerEmulator = None
    DisplayType = None
    DisplayAlignment = None
    DisplayLine = None

# Import the simplified hardware manager
try:
    from .hardware_manager import HardwareManager, create_hardware_manager
    HARDWARE_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Hardware manager not available: {e}")
    HARDWARE_MANAGER_AVAILABLE = False
    HardwareManager = None
    create_hardware_manager = None

__all__ = [
    'ButtonController', 
    'ButtonControllerEmulator',
    'ButtonType', 
    'ButtonEvent',
    'DisplayController',
    'DisplayControllerEmulator', 
    'DisplayType',
    'DisplayAlignment',
    'DisplayLine',
    'HardwareManager',
    'create_hardware_manager',
    'BUTTON_CONTROLLER_AVAILABLE',
    'DISPLAY_CONTROLLER_AVAILABLE',
    'HARDWARE_MANAGER_AVAILABLE'
]
