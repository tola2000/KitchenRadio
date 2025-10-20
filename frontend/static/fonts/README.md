# KitchenRadio Font - HomeVideo

The KitchenRadio uses only the **HomeVideo** font for a consistent retro/vintage aesthetic.

## Required Font - HomeVideo

- **File name**: `homevideo.ttf` (or variations like `HomeVideo.ttf`)
- **Style**: Retro/vintage display font perfect for kitchen radio
- **Required**: Place the HomeVideo font file in this folder

## Supported File Names

The system will automatically detect these HomeVideo font variations:
- `homevideo.ttf`
- `HomeVideo.ttf` 
- `homevideo-regular.ttf`
- `HomeVideo-Regular.ttf`
- `.otf` versions of the above

## Setup Instructions

1. **Get the HomeVideo font** (homevideo.ttf)
2. **Copy it** to this `frontend/static/fonts/` folder
3. **Restart the application** - it will automatically load the font
4. **Check the logs** to confirm: "HomeVideo font loaded successfully"

## Fallback

If HomeVideo font is not found, the system will use the default system font and display a warning in the logs: "HomeVideo font not found - place homevideo.ttf in frontend/static/fonts/ folder"

## Why HomeVideo Only?

- **Consistent retro aesthetic** across all display elements
- **Simplified font management** - no complex fallback chains  
- **Kitchen radio theme** - perfect vintage look for the project
- **Easy deployment** - just one font file needed
