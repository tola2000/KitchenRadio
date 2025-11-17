# KitchenRadio Architecture Refactoring Plan

## Overview

Refactor KitchenRadio to separate backend/source management logic into a dedicated `SourceController` class. This creates a cleaner architecture where DisplayController and ButtonController interact with SourceController instead of KitchenRadio directly.

**Date:** November 17, 2025

---

## Current Architecture Problems

### 1. **God Object Anti-Pattern**
- KitchenRadio does everything: backend management, playback control, volume, source switching
- 1700+ lines in single class
- Hard to test individual concerns
- Tight coupling between UI controllers and backend logic

### 2. **Unclear Responsibilities**
```python
# DisplayController and ButtonController both reference KitchenRadio
button_controller = ButtonController(kitchen_radio=kitchen_radio)
display_controller = DisplayController(kitchen_radio=kitchen_radio)

# But they only need playback/volume control, not backend management
```

### 3. **Difficult to Extend**
- Adding new backend requires modifying large KitchenRadio class
- Backend-specific logic mixed with coordination logic

---

## Proposed Architecture

### New Class Structure

```
kitchenradio/
├── radio/
│   ├── sources/                    # NEW PACKAGE
│   │   ├── __init__.py
│   │   └── source_controller.py   # NEW: Manages all backends
│   ├── kitchen_radio.py            # REFACTORED: Thin facade
│   └── hardware/
│       ├── button_controller.py    # UPDATED: Uses SourceController
│       └── display_controller.py   # UPDATED: Uses SourceController
```

### Responsibility Split

**SourceController** (NEW):
- Manages all music backends (MPD, Librespot, Bluetooth)
- Handles backend initialization and connection
- Provides unified playback control (play, pause, stop, next, previous)
- Provides unified volume control (up, down, set, get)
- Manages source switching and exclusive playback
- Handles backend-specific menu options
- **NO UI concerns**
- **NO callback system** (KitchenRadio owns that)

**KitchenRadio** (REFACTORED):
- Thin facade that owns SourceController
- Manages callbacks and event propagation
- Provides backward-compatible API
- Delegates all playback/volume to SourceController
- **NO backend-specific logic**
- **NO direct backend access**

**ButtonController** (UPDATED):
- References SourceController instead of KitchenRadio
- Calls SourceController methods for playback/volume
- May reference KitchenRadio for status/callbacks

**DisplayController** (UPDATED):
- References SourceController instead of KitchenRadio  
- Calls SourceController for status updates
- May reference KitchenRadio for callbacks

---

## Methods to Move

### From KitchenRadio → SourceController

#### Backend Management
- `_initialize_backends()` → `initialize()`
- `_initialize_mpd()` → `_initialize_mpd()`
- `_initialize_librespot()` → `_initialize_librespot()`
- `_initialize_bluetooth()` → `_initialize_bluetooth()`
- `_reconnect_mpd()` → `_reconnect_mpd()`
- `_reconnect_librespot()` → `_reconnect_librespot()`

#### Source Control
- `set_source(source)` → `set_source(source)`
- `get_current_source()` → `get_current_source()`
- `get_available_sources()` → `get_available_sources()`
- `switch_to_mpd()` → `switch_to_mpd()`
- `switch_to_spotify()` → `switch_to_spotify()`
- `_stop_source(source)` → `_stop_source(source)`
- `_get_active_controller()` → `_get_active_controller()`

#### Playback Control
- `play()` → `play()`
- `pause()` → `pause()`
- `stop_play()` → `stop()`
- `play_pause()` → `play_pause()`
- `next()` → `next()`
- `previous()` → `previous()`

#### Volume Control
- `volume_up(step)` → `volume_up(step)`
- `volume_down(step)` → `volume_down(step)`
- `set_volume(volume)` → `set_volume(volume)`
- `get_volume()` → `get_volume()`

#### Menu/Options
- `get_menu_options()` → `get_menu_options()`
- `execute_menu_action(action, params)` → `execute_menu_action(action, params)`

#### Power Management
- `power_on()` → `power_on()`
- `power_off()` → `power_off()`
- `_power_on()` → `_power_on()`
- `_power_off()` → `_power_off()`

#### Status
- Parts of `get_status()` → `get_source_status()`

---

## Methods to Keep in KitchenRadio

### Facade Methods (Delegate to SourceController)
```python
def play(self) -> bool:
    """Delegate to SourceController"""
    return self.source_controller.play()

def volume_up(self, step: int = 5) -> Optional[int]:
    """Delegate to SourceController"""  
    return self.source_controller.volume_up(step)
```

### Callback Management
- `add_callback(event, callback)`
- `remove_callback(event, callback)`
- `_notify_callbacks(event, **kwargs)`

### Lifecycle
- `start()` - Initialize SourceController and start monitoring
- `stop()` - Stop SourceController and cleanup
- `_signal_handler(signum, frame)`

### Status Aggregation
- `get_status()` - Aggregate from SourceController + own state

---

## Implementation Steps

### Phase 1: Create SourceController ✓
1. Create `kitchenradio/radio/sources/` package
2. Create `source_controller.py` with class skeleton
3. Move BackendType enum to source_controller.py
4. Add __init__.py exports

### Phase 2: Move Backend Management
1. Move backend initialization methods
2. Move backend connection/reconnection logic
3. Move monitor setup (keep in KitchenRadio for now)

### Phase 3: Move Playback Control
1. Move play/pause/stop methods
2. Move next/previous methods
3. Move `_get_active_controller()` helper

### Phase 4: Move Volume Control
1. Move volume_up/volume_down
2. Move set_volume/get_volume

### Phase 5: Move Source Management
1. Move source switching logic
2. Move power on/off logic
3. Move source selection

### Phase 6: Move Menu Logic
1. Move get_menu_options
2. Move execute_menu_action

### Phase 7: Refactor KitchenRadio
1. Create SourceController instance
2. Replace method implementations with delegation
3. Keep callback system
4. Keep lifecycle management

### Phase 8: Update Controllers
1. Update ButtonController to accept SourceController
2. Update DisplayController to accept SourceController
3. Update method calls to use SourceController

### Phase 9: Update Daemon
1. Update run_daemon.py initialization
2. Pass SourceController to controllers
3. Test all modes

### Phase 10: Documentation
1. Create architecture diagram
2. Update API documentation
3. Create migration guide

---

## API Examples

### Old API (Current)
```python
# Everything through KitchenRadio
kitchen_radio = KitchenRadio()
kitchen_radio.start()
kitchen_radio.set_source(BackendType.MPD)
kitchen_radio.play()
kitchen_radio.volume_up(5)

# Controllers use KitchenRadio
button_controller = ButtonController(kitchen_radio=kitchen_radio)
display_controller = DisplayController(kitchen_radio=kitchen_radio)
```

### New API (After Refactoring)
```python
# KitchenRadio owns SourceController
kitchen_radio = KitchenRadio()
kitchen_radio.start()  # Initializes source_controller internally

# Backward compatible - still works through KitchenRadio
kitchen_radio.set_source(BackendType.MPD)
kitchen_radio.play()
kitchen_radio.volume_up(5)

# Controllers can use SourceController directly
source_controller = kitchen_radio.source_controller
button_controller = ButtonController(source_controller=source_controller)
display_controller = DisplayController(source_controller=source_controller)

# Or keep backward compatibility
button_controller = ButtonController(kitchen_radio=kitchen_radio)
# Internally extracts: self.source_controller = kitchen_radio.source_controller
```

---

## Benefits

### 1. **Separation of Concerns**
- Backend management isolated in SourceController
- KitchenRadio focuses on coordination and callbacks
- UI controllers only reference what they need

### 2. **Testability**
- Test SourceController backend logic independently
- Mock SourceController for UI controller tests
- Smaller, focused test suites

### 3. **Maintainability**
- Smaller classes (KitchenRadio ~500 lines, SourceController ~800 lines)
- Clear boundaries between responsibilities
- Easier to locate and fix bugs

### 4. **Extensibility**
- Add new backend by modifying only SourceController
- UI controllers unaffected by backend changes
- Easy to add backend-specific features

### 5. **Reusability**
- SourceController usable without full KitchenRadio
- CLI tools can use SourceController directly
- Testing utilities simpler

---

## Backward Compatibility

### Maintained ✓
- All existing KitchenRadio methods work (delegate to SourceController)
- Callback system unchanged
- get_status() return format unchanged
- Existing code using KitchenRadio continues to work

### New Options ✓
- Controllers can reference SourceController directly
- More flexible initialization patterns
- Clearer API for new code

---

## Risks and Mitigations

### Risk 1: Breaking Existing Code
**Mitigation**: Keep KitchenRadio as facade with delegation. All existing calls work.

### Risk 2: Complex Callback Propagation
**Mitigation**: Keep callback system in KitchenRadio. SourceController doesn't handle callbacks.

### Risk 3: State Synchronization
**Mitigation**: SourceController owns all backend state. KitchenRadio queries SourceController.

### Risk 4: Large Change Surface
**Mitigation**: Incremental approach with testing after each phase.

---

## Success Criteria

✅ All existing tests pass  
✅ run_daemon.py works with all component combinations  
✅ DisplayController and ButtonController work correctly  
✅ Web API continues to function  
✅ No performance regression  
✅ Code coverage maintained or improved  

---

## Timeline Estimate

- Phase 1: Create SourceController skeleton - 30 min
- Phase 2-6: Move methods incrementally - 2-3 hours
- Phase 7: Refactor KitchenRadio - 1 hour
- Phase 8: Update controllers - 1 hour  
- Phase 9: Update daemon - 30 min
- Phase 10: Documentation - 1 hour

**Total**: 6-7 hours

---

## Next Steps

1. Review and approve this plan
2. Start Phase 1: Create SourceController skeleton
3. Proceed incrementally with testing
4. Update documentation as we go

