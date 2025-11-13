# Clock, Volume, and Menu Not Showing - Root Cause Analysis

## Problem
Clock, volume, and menu displays are not rendering on the screen.

## Root Cause

### The Bug
The code had a conditional that tried to capture a return value from `render_frame()` for non-track_info displays:

```python
# BROKEN CODE
if display_type == 'track_info':
    self.display_interface.render_frame(draw_func)
    if isinstance(truncation_info, dict):
        # ... process truncation info
else:
    # BUG: render_frame() returns None!
    truncation_info = self.display_interface.render_frame(draw_func)
    if isinstance(truncation_info, dict):
        # ... this condition is always False because truncation_info = None
```

### Why It Failed

1. **`render_frame()` returns `None`**:
   ```python
   def render_frame(self, draw_func: Callable[[ImageDraw.Draw], None]):
       # ... rendering code ...
       # No return statement = returns None
   ```

2. **Formatter return types vary**:
   - `format_track_info()` → Returns `(draw_func, truncation_info)` tuple
   - `format_status_message()` → Returns `(draw_func, truncation_info)` tuple
   - `format_clock_display()` → Returns `draw_func` only (Callable)
   - `format_volume_display()` → Returns `draw_func` only (Callable)
   - `format_menu_display()` → Returns `draw_func` only (Callable)

3. **The flow for clock/volume/menu**:
   ```
   format_clock_display() → returns draw_func (Callable)
   ↓
   truncation_info remains None (from unpacking)
   ↓
   truncation_info = render_frame(draw_func) → assigns None
   ↓
   if isinstance(None, dict): → False, never processes
   ```

4. **Result**: The displays rendered but immediately got overwritten or failed silently because the return value handling was incorrect.

## The Fix

```python
# FIXED CODE
# Render the display (render_frame returns None)
self.display_interface.render_frame(draw_func)

# Update truncation info if available (only from track_info and status_message)
if truncation_info and isinstance(truncation_info, dict):
    self.last_truncation_info.update(truncation_info)
    self._update_scroll_offsets(truncation_info)
```

### Why This Works

1. **Always call `render_frame()` directly** - Don't try to capture its return value
2. **Check if `truncation_info` exists** - Only process if the formatter returned it
3. **Unified logic** - Same code path for all display types
4. **Clearer intent** - Separates rendering from truncation processing

## Display Type Reference

| Display Type | Formatter Method | Returns | Has Truncation? |
|-------------|------------------|---------|-----------------|
| `track_info` | `format_track_info()` | `(draw_func, trunc_info)` | ✅ Yes |
| `status_message` | `format_status_message()` | `(draw_func, trunc_info)` | ✅ Yes |
| `clock` | `format_clock_display()` | `draw_func` | ❌ No |
| `volume` | `format_volume_display()` | `draw_func` | ❌ No |
| `menu` | `format_menu_display()` | `draw_func` | ❌ No |
| `simple_text` | `format_simple_text()` | `draw_func` | ❌ No |
| `error_message` | `format_error_message()` | `draw_func` | ❌ No |

## Testing

Test each display type:

```python
# Test clock
display_controller._render_clock_display()
# Should show current time

# Test volume
display_controller._render_volume_overlay(50)
# Should show volume bar at 50%

# Test menu
menu_data = {
    'title': 'Test Menu',
    'menu_items': ['Item 1', 'Item 2', 'Item 3'],
    'selected_index': 0
}
display_controller._render_display_content('menu', menu_data)
# Should show menu with selection

# Test track info (regression test)
track_data = {
    'title': 'Test Song',
    'artist': 'Test Artist',
    'album': 'Test Album',
    'playing': True,
    'volume': 75,
    'scroll_offsets': {}
}
display_controller._render_display_content('track_info', track_data)
# Should still work with scrolling
```

## Key Learnings

1. **Don't assume return values** - Check method signatures carefully
2. **Formatters have different return types** - Some return tuples, some return single values
3. **Rendering is a side effect** - `render_frame()` doesn't return data
4. **Truncation info is optional** - Only needed for scrolling text (track_info, status_message)

## Summary

**Problem**: Tried to capture `None` from `render_frame()` and assign it to `truncation_info`, causing clock, volume, and menu to not display properly.

**Solution**: Always call `render_frame()` directly without capturing return value. Only process `truncation_info` if it was set by the formatter.

**Result**: All display types now work correctly! ✅
