# Button Hardware Integration

## Overview
The ButtonController now supports **hardware buttons via MCP23017 GPIO expander** with proper debouncing logic integrated from the working button_test.py.

## Hardware Configuration

### MCP23017 I2C Address
- Default: `0x27`
- Configurable via `i2c_address` parameter

### Pin Assignments

All buttons connect between MCP23017 pins and **GND** (active-low with internal pull-ups).

#### Port A (GPA0-GPA7) - Source and Menu Buttons
| Pin  | Button Type      | Description        |
|------|------------------|--------------------|
| GPA0 | SOURCE_MPD       | Switch to MPD      |
| GPA1 | SOURCE_SPOTIFY   | Switch to Spotify  |
| GPA2 | MENU_UP          | Menu navigation up |
| GPA3 | MENU_DOWN        | Menu navigation down |
| GPA4 | MENU_TOGGLE      | Toggle menu        |
| GPA5 | MENU_SET         | Set menu option    |
| GPA6 | MENU_OK          | Confirm selection  |
| GPA7 | MENU_EXIT        | Exit menu          |

#### Port B (GPB0-GPB7) - Transport, Volume, and Power Buttons
| Pin  | Button Type           | Description           |
|------|-----------------------|-----------------------|
| GPB0 | TRANSPORT_PREVIOUS    | Previous track        |
| GPB1 | TRANSPORT_PLAY_PAUSE  | Play/Pause toggle     |
| GPB2 | TRANSPORT_STOP        | Stop playback         |
| GPB3 | TRANSPORT_NEXT        | Next track            |
| GPB4 | VOLUME_DOWN           | Decrease volume       |
| GPB5 | VOLUME_UP             | Increase volume       |
| GPB6 | POWER                 | Power on/off          |
| GPB7 | (unused)              | Available for future  |

### Wiring
Each button requires 2 connections:
1. **One side** → MCP23017 pin (see table above)
2. **Other side** → **GND** (ground)

**Internal pull-up resistors** are enabled in software, so no external resistors needed.

## Software Features

### Debounce Logic
- **Debounce Time**: 50ms (configurable)
- **Method**: State must remain stable for debounce period before acceptance
- **Bounce Rejection**: Changes that revert before debounce are ignored

### Dual Mode Operation
The controller supports both:
1. **Hardware Mode** (with MCP23017)
   - Auto-detects hardware availability
   - Monitors buttons in background thread
   - 10ms polling interval
   
2. **Software Mode** (fallback)
   - Programmatic button control via `press_button(button_name)`
   - Used for web interface and testing

## Usage

### Initialization
```python
from radio.hardware import ButtonController
from radio.kitchen_radio import KitchenRadio

# Create controller with hardware support
controller = ButtonController(
    kitchen_radio=radio_instance,
    use_hardware=True,      # Enable MCP23017 hardware
    i2c_address=0x27,       # MCP23017 I2C address
    debounce_time=0.05,     # 50ms debounce
    display_controller=display
)

# Initialize hardware
success = controller.initialize()
```

### Hardware Auto-Detection
If hardware libraries are not available or hardware initialization fails:
- Automatically falls back to software mode
- No code changes needed
- Logs warning message

### Manual Button Control (Software Mode)
```python
# Programmatically press buttons (for web interface)
controller.press_button("transport_play_pause")
controller.press_button("volume_up")
```

## Implementation Details

### State Machine
Each button maintains state:
- `last_state`: Last accepted state (True=HIGH/not pressed, False=LOW/pressed)
- `pending_state`: State waiting for debounce confirmation
- `pending_since`: Timestamp when pending state was first detected

### Debounce Algorithm
1. **State Change Detected**: Current state ≠ last_state
2. **Start Timer**: Set pending_state and pending_since
3. **Wait for Stability**: Check if state remains pending for debounce_time
4. **Accept or Reject**:
   - If stable → Accept change, trigger action
   - If reverts → Reject as bounce, clear pending

### Thread Safety
- Background monitoring thread polls buttons every 10ms
- Thread-safe state updates
- Clean shutdown with thread join

## Testing

### Test Script
The `button_test.py` script was used to develop and verify the debounce logic:
- Tests single button on GPA0
- Logs state changes and timing
- Validates pull-up configuration

### Verification
1. Check pull-up registers (GPPU) are set correctly
2. Initial state should be HIGH (True) with no button pressed
3. Button press changes state to LOW (False)
4. Bounces shorter than 50ms are rejected

## Dependencies

### Required Hardware Libraries (Raspberry Pi)
```
adafruit-circuitpython-mcp230xx
adafruit-blinka
```

Install via:
```bash
pip install adafruit-circuitpython-mcp230xx
```

### Graceful Degradation
If libraries not installed:
- `HARDWARE_AVAILABLE = False`
- Controller runs in software mode
- No errors or crashes

## Troubleshooting

### Buttons Not Responding
1. Check wiring (button to pin and GND)
2. Verify I2C address (default 0x27)
3. Check logs for hardware initialization
4. Run `button_test.py` on individual pin

### False Triggers / Bouncing
1. Increase `debounce_time` (try 0.1 or 0.2)
2. Add hardware capacitor (0.1µF) across button
3. Check for loose connections
4. Shield button wires from noise sources

### Pull-up Not Working
1. Check GPPU register values in logs
2. Verify Pin.UP is being used
3. Test with multimeter (pin should read ~3.3V when not pressed)

## Future Enhancements
- Long press detection for volume buttons
- Configurable pin mappings
- Interrupt-based detection (vs polling)
- Button combination detection
