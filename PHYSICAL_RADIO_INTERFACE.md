# KitchenRadio Physical Interface

## Overview

The KitchenRadio Physical Interface is designed to look and feel like a real physical radio with an OLED display and physical buttons. This interface provides intuitive control over both MPD and Spotify music sources.

## Layout

```
    [MPD]    [Spotify]    [OFF]         <- Source Selection
    
[UP ]                            [SET ]
[MENU]     [OLED DISPLAY]        [OK  ]  <- Menu Navigation
[DOWN]                           [EXIT]

    [◄◄]   [►/❚❚]  [■]    [►►]        <- Transport Controls
    
    [VOL-]  ▓▓▓▓░░░░░░  [VOL+]         <- Volume Control
```

## Features

### OLED Display
- Shows current track information (title, artist, album)
- Displays source status and connection info
- Shows menus when activated
- Real-time updates of playback status

### Source Controls
- **MPD Button**: Switches to MPD music server
- **Spotify Button**: Switches to Spotify (via librespot)
- **OFF Button**: Turns off the radio
- **Double-press**: Shows source-specific menu

### Menu System
- **UP/DOWN**: Navigate through menu options
- **MENU**: Toggle menu visibility
- **OK**: Select current menu option
- **EXIT**: Close menu
- **SET**: Additional settings (future expansion)

### Transport Controls
- **Previous (◄◄)**: Skip to previous track
- **Play/Pause (►/❚❚)**: Toggle playback
- **Stop (■)**: Stop playback
- **Next (►►)**: Skip to next track

### Volume Controls
- **VOL-**: Decrease volume
- **VOL+**: Increase volume
- **Volume Bar**: Visual representation of current volume

## Menu Options

### MPD Menu
When MPD is the active source, pressing the MPD button again shows:
- List of available playlists
- Navigate with UP/DOWN buttons
- Select with OK button to load and play playlist

### Spotify Menu
When Spotify is the active source, pressing the Spotify button again shows:
- **Shuffle**: Toggle shuffle mode on/off
- **Repeat**: Cycle through repeat modes (Off → Track → Context → Off)
- Navigate with UP/DOWN buttons
- Select with OK button to toggle setting

## Usage

1. **Select a Source**: Press MPD or Spotify button to activate
2. **Control Playback**: Use transport buttons to play, pause, skip tracks
3. **Adjust Volume**: Use VOL+/VOL- buttons or visual slider
4. **Access Menus**: Press active source button again to show menu
5. **Navigate Menus**: Use UP/DOWN to browse, OK to select, EXIT to close

## Technical Details

### Files
- `frontend/templates/radio_interface.html` - Physical radio HTML layout
- `frontend/static/css/radio_style.css` - Radio styling and animations
- `frontend/static/js/radio_app.js` - Radio interface JavaScript
- `kitchenradio/radio/kitchen_radio.py` - Backend menu system
- `kitchenradio/web/kitchen_radio_web.py` - Web API endpoints

### API Endpoints
- `GET /api/menu` - Get menu options for active source
- `POST /api/menu/action` - Execute menu action
- `GET /radio` - Access physical radio interface
- All existing playback and volume control endpoints

### Styling
- Dark theme with green OLED-style display
- Physical button appearance with shadows and gradients
- Responsive design for different screen sizes
- Smooth animations and transitions

## Testing

Run the test script to see the interface in action:

```bash
python test_radio_interface.py
```

This will start the web server and open the physical radio interface in your browser.

## Browser Compatibility

The interface works best in modern browsers that support:
- CSS Grid and Flexbox
- CSS transforms and animations
- ES6 JavaScript features
- Fetch API for backend communication

Tested on Chrome, Firefox, Safari, and Edge.
