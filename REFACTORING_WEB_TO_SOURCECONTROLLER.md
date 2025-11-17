# Web Interface Refactoring - SourceController Migration

## Overview
Completed refactoring of `kitchen_radio_web.py` to use `SourceController` directly instead of relying on the `KitchenRadio` facade. This aligns with the overall architecture where all UI components (Button, Display, Web) use SourceController directly for cleaner separation of concerns.

## Changes Made

### 1. Updated `kitchen_radio_web.py`

#### Import Changes
```python
# Before:
from kitchenradio.kitchen_radio import KitchenRadio

# After:
from kitchenradio.sources.source_controller import SourceController, BackendType
```

#### Constructor Changes
```python
# Before:
def __init__(self, 
             kitchen_radio: 'KitchenRadio',
             display_controller = None,
             button_controller = None,
             host: str = '0.0.0.0',
             port: int = 5001):
    self.kitchen_radio = kitchen_radio

# After:
def __init__(self, 
             source_controller: 'SourceController',
             display_controller = None,
             button_controller = None,
             kitchen_radio = None,  # Optional, for daemon operations only
             host: str = '0.0.0.0',
             port: int = 5001):
    self.source_controller = source_controller
    self.kitchen_radio = kitchen_radio  # Optional, only for reconnect_backends
```

#### Method Call Replacements (6 locations)
All `self.kitchen_radio.get_status()` calls replaced with `self.source_controller.get_status()`:
- Line ~169: Button press display update
- Line ~249: API status endpoint
- Line ~454: Menu API current source check
- Line ~592: Display update endpoint

All `self.kitchen_radio.set_source()` calls replaced with `self.source_controller.set_source()`:
- Line ~525: Switch to MPD source
- Line ~541: Switch to Spotify source

#### Daemon Operation Handling
`reconnect_backends()` calls kept using optional `kitchen_radio` parameter with guard:
```python
if not self.kitchen_radio:
    return jsonify({
        'success': False,
        'message': 'KitchenRadio instance not available for reconnect operation'
    }), 503

results = self.kitchen_radio.reconnect_backends()
```

Locations:
- Line ~277: API reconnect endpoint
- Line ~514: Menu reconnect action

#### Standalone Test Mode Update
```python
# Before:
kitchen_radio = KitchenRadio()
display_controller = DisplayController(kitchen_radio=kitchen_radio, ...)
button_controller = ButtonController(kitchen_radio=kitchen_radio, ...)
api = KitchenRadioWeb(kitchen_radio=kitchen_radio, ...)

# After:
kitchen_radio = KitchenRadio()
source_controller = kitchen_radio.source_controller  # Extract SourceController
display_controller = DisplayController(source_controller=source_controller, ...)
button_controller = ButtonController(source_controller=source_controller, ...)
api = KitchenRadioWeb(
    source_controller=source_controller,
    kitchen_radio=kitchen_radio,  # For reconnect_backends
    ...
)
```

### 2. Updated `run_daemon.py`

#### Architecture Change
```python
# Before:
kitchen_radio = KitchenRadio()
display_controller = DisplayController(kitchen_radio=kitchen_radio, ...)
button_controller = ButtonController(kitchen_radio=kitchen_radio, ...)
web_server = KitchenRadioWeb(kitchen_radio=kitchen_radio, ...)

# After:
kitchen_radio = KitchenRadio()
source_controller = kitchen_radio.source_controller  # Extract for direct access

display_controller = DisplayController(source_controller=source_controller, ...)
button_controller = ButtonController(source_controller=source_controller, ...)
web_server = KitchenRadioWeb(
    source_controller=source_controller,
    kitchen_radio=kitchen_radio,  # For daemon operations
    ...
)
```

## Architecture Summary

### New Component Relationships
```
KitchenRadio (Minimal Facade ~400 lines)
├── Owns: SourceController
├── Manages: Daemon lifecycle, callbacks, system operations
└── Provides: No delegation methods (all removed)

SourceController (810 lines)
├── Backend management (MPD, Librespot, Bluetooth)
├── Playback control (play, pause, stop, next, previous)
├── Volume control (get, set, up, down)
├── Source management (get, set, switch)
└── Status aggregation (get_status from all backends)

UI Components (all use SourceController directly):
├── ButtonController → source_controller ✅
├── DisplayController → source_controller ✅
└── KitchenRadioWeb → source_controller ✅
    └── Optional kitchen_radio reference for reconnect_backends only
```

### Design Principles
1. **Direct Access**: All UI components use SourceController directly (no delegation layer)
2. **Minimal Facade**: KitchenRadio only manages daemon lifecycle and forwards callbacks
3. **Clean Separation**: Backend logic in SourceController, daemon logic in KitchenRadio
4. **Flexible Initialization**: run_daemon.py orchestrates component wiring

## Benefits

1. **Cleaner Architecture**: No delegation methods cluttering KitchenRadio facade
2. **Consistent Pattern**: All UI components use same access pattern (direct SourceController)
3. **Better Performance**: Direct access eliminates delegation overhead
4. **Easier Testing**: UI components can be tested with SourceController mock
5. **Clear Responsibilities**: 
   - KitchenRadio = Daemon lifecycle + callbacks
   - SourceController = Backend management + control
   - UI Components = User interaction

## Migration Notes

### For Developers
If you have custom code using `kitchen_radio`:

**Before:**
```python
kitchen_radio = KitchenRadio()
kitchen_radio.start()

# Access via delegation
status = kitchen_radio.get_status()
kitchen_radio.set_volume(50)
kitchen_radio.play()
```

**After:**
```python
kitchen_radio = KitchenRadio()
kitchen_radio.start()

# Access SourceController directly
source_controller = kitchen_radio.source_controller
status = source_controller.get_status()
source_controller.set_volume(50)
source_controller.play()
```

### For Web API Users
No changes required - all API endpoints remain the same. Internal implementation now uses SourceController.

## Testing Checklist

- [ ] Run standalone web mode: `python kitchenradio/interfaces/web/kitchen_radio_web.py`
- [ ] Run daemon with web: `python run_daemon.py --web`
- [ ] Test playback controls via web API
- [ ] Test volume control via web API
- [ ] Test source switching via web API
- [ ] Test status display via web API
- [ ] Test menu operations
- [ ] Test reconnect_backends endpoint
- [ ] Verify button controller integration
- [ ] Verify display controller integration

## Files Modified

1. `kitchenradio/interfaces/web/kitchen_radio_web.py` (907 → 928 lines)
   - Changed constructor to accept `source_controller` instead of `kitchen_radio`
   - Replaced 6 `get_status()` calls
   - Replaced 2 `set_source()` calls
   - Added guards for optional `reconnect_backends()` calls
   - Updated standalone test mode

2. `run_daemon.py` (248 → 251 lines)
   - Extract `source_controller` from `kitchen_radio`
   - Pass `source_controller` to all UI components
   - Pass optional `kitchen_radio` to web for daemon operations

## Completion Status

✅ Web interface refactored to use SourceController
✅ run_daemon.py updated with new wiring
✅ Standalone test mode updated
✅ All compilation errors resolved
✅ Architecture documentation updated

**Next Steps:**
1. Test all functionality with the new architecture
2. Update USER_GUIDE.md with architecture diagrams
3. Create SOURCE_CONTROLLER.md documenting the design
