"""
KitchenRadio Hardware Controllers Package

Hardware interface controllers for KitchenRadio physical radio interface.
Supports both real Raspberry Pi hardware and built-in emulators.
"""

import logging

logger = logging.getLogger(__name__)

# Import button controller components
try:
    from .button_controller import ButtonController, ButtonType, ButtonEvent
    BUTTON_CONTROLLER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Button controller not available: {e}")
    BUTTON_CONTROLLER_AVAILABLE = False
    ButtonController = None
    ButtonType = None
    ButtonEvent = None

# Import display components
try:
    from .display_controller import DisplayController
    from .display_interface import DisplayInterface
    from .display_formatter import DisplayFormatter
    DISPLAY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Display components not available: {e}")
    DISPLAY_AVAILABLE = False
    DisplayController = None
    DisplayInterface = None
    DisplayFormatter = None

__all__ = [
    # Button controller
    'ButtonController', 
    'ButtonType', 
    'ButtonEvent',
    'BUTTON_CONTROLLER_AVAILABLE',
    
    # Display components
    'DisplayController',
    'DisplayInterface',
    'DisplayFormatter',
    'DISPLAY_AVAILABLE',
]
