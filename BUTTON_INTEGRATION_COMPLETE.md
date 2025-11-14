# Button Controller Hardware Integration - Complete

## Summary
All buttons are now properly integrated with MCP23017 GPIO hardware support.

## Button Pin Assignments and Actions

### ✅ All 15 Buttons Configured

| Button Type           | Pin  | Port | Handler Method      | Action                      |
|-----------------------|------|------|---------------------|-----------------------------|
| SOURCE_MPD            | 0    | GPA0 | `_select_mpd`       | Switch to MPD source        |
| SOURCE_SPOTIFY        | 1    | GPA1 | `_select_spotify`   | Switch to Spotify source    |
| MENU_UP               | 2    | GPA2 | `_menu_up`          | Navigate menu up            |
| MENU_DOWN             | 3    | GPA3 | `_menu_down`        | Navigate menu down          |
| MENU_TOGGLE           | 4    | GPA4 | `_menu_toggle`      | Show/hide menu              |
| MENU_SET              | 5    | GPA5 | `_menu_set`         | Confirm menu selection      |
| MENU_OK               | 6    | GPA6 | `_menu_ok`          | Confirm menu selection      |
| MENU_EXIT             | 7    | GPA7 | `_menu_exit`        | Exit menu, hide overlay     |
| TRANSPORT_PREVIOUS    | 8    | GPB0 | `_previous`         | Previous track              |
| TRANSPORT_PLAY_PAUSE  | 9    | GPB1 | `_play_pause`       | Toggle play/pause           |
| TRANSPORT_STOP        | 10   | GPB2 | `_stop`             | Stop playback               |
| TRANSPORT_NEXT        | 11   | GPB3 | `_next`             | Next track                  |
| VOLUME_DOWN           | 12   | GPB4 | `_volume_down`      | Decrease volume (-5)        |
| VOLUME_UP             | 13   | GPB5 | `_volume_up`        | Increase volume (+5)        |
| POWER                 | 14   | GPB6 | `_power`            | Power on/off                |

## Handler Implementation

### Source Buttons
- **SOURCE_MPD**: Calls `kitchen_radio.set_source(BackendType.MPD)`
- **SOURCE_SPOTIFY**: Calls `kitchen_radio.set_source(BackendType.LIBRESPOT)`

### Transport Buttons
- **TRANSPORT_PLAY_PAUSE**: Calls `kitchen_radio.play_pause()`
- **TRANSPORT_STOP**: Calls `kitchen_radio.stop_play()`
- **TRANSPORT_NEXT**: Calls `kitchen_radio.next()`
- **TRANSPORT_PREVIOUS**: Calls `kitchen_radio.previous()`

### Volume Buttons
- **VOLUME_UP**: Calls `kitchen_radio.volume_up(step=5)` + shows volume overlay
- **VOLUME_DOWN**: Calls `kitchen_radio.volume_down(step=5)` + shows volume overlay

### Menu Buttons
- **MENU_UP**: Navigate to previous menu item (scroll up)
- **MENU_DOWN**: Navigate to next menu item (scroll down)
- **MENU_TOGGLE**: Show menu overlay with current options
- **MENU_SET**: Confirm current selection (same as OK)
- **MENU_OK**: Execute selected menu item via `_on_menu_item_selected()`
- **MENU_EXIT**: Hide menu overlay via `display_controller.hide_overlay()`

### Power Button
- **POWER**: Calls `kitchen_radio.power()` to stop all playback

## Hardware Configuration

### MCP23017 Setup
```python
controller = ButtonController(
    kitchen_radio=radio_instance,
    use_hardware=True,
    i2c_address=0x27,
    debounce_time=0.05
)
```

### Pin Configuration
All pins configured as:
- **Direction**: Input
- **Pull resistor**: Pull-up (internal)
- **Active state**: Low (button pressed = GND connection)

### Initialization Process
1. Create I2C bus connection
2. Initialize MCP23017 at address 0x27
3. Configure each pin in BUTTON_PIN_MAP
4. Enable internal pull-up resistors
5. Verify GPPU registers
6. Start background monitoring thread

## Debounce Logic

### State Machine Per Button
- `last_state`: Last stable state (True=HIGH/not pressed)
- `pending_state`: State waiting for confirmation
- `pending_since`: Timestamp of state change detection

### Algorithm
1. Poll button at 10ms intervals
2. Detect state change (current ≠ last)
3. Start debounce timer on new change
4. Wait 50ms for state stability
5. Accept change if stable, reject if bounces back
6. Execute action on accepted press event

## Complete Integration Checklist

- ✅ All 15 ButtonType enum entries defined
- ✅ All 15 buttons in BUTTON_PIN_MAP with pin assignments
- ✅ All 15 buttons in button_actions with handler methods
- ✅ All handler methods implemented
- ✅ Hardware initialization in _initialize_hardware()
- ✅ Background monitoring thread in _monitor_buttons()
- ✅ Debounce logic in _check_button_state()
- ✅ Pull-up resistors enabled on all pins
- ✅ Clean shutdown with thread join
- ✅ Graceful fallback to software mode

## Testing

### Hardware Test
1. Connect buttons between pins and GND
2. Run KitchenRadio with hardware enabled
3. Press each button and verify action
4. Check logs for "Button pressed: button_name"

### Verify Configuration
Check logs at startup:
```
INFO: MCP23017 found at address 0x27
DEBUG: Configured source_mpd on pin 0
DEBUG: Configured source_spotify on pin 1
...
INFO: Pull-up registers: Port A=0xFF, Port B=0x7F
INFO: Button monitoring thread started
```

### Test Each Button
1. **Source buttons**: Switch between MPD and Spotify
2. **Transport**: Control playback (play/pause/stop/next/prev)
3. **Volume**: Adjust volume and see overlay
4. **Menu**: Navigate, select, and exit menus
5. **Power**: Stop all playback

## Status
🟢 **COMPLETE** - All buttons connected, configured, and functional
