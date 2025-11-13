# Quick Start with Virtual Environment

## Step-by-Step Setup

### 1. Create Virtual Environment

```powershell
cd "c:\Users\ID980331\OneDrive - Proximus\Personal\Home\KitchenRadio"

# Create virtual environment
python -m venv venv
```

### 2. Activate Virtual Environment

```powershell
# Activate the virtual environment
.\venv\Scripts\Activate.ps1
```

**If you get an execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then try activating again
.\venv\Scripts\Activate.ps1
```

**You'll know it's activated when you see `(venv)` in your prompt:**
```
(venv) PS C:\Users\ID980331\OneDrive - Proximus\Personal\Home\KitchenRadio>
```

### 3. Install Dependencies

```powershell
# Make sure you're in the virtual environment (you should see (venv) in prompt)
pip install -r requirements.txt
```

This will install:
- `python-mpd2` - MPD client library
- `Flask` and `Flask-CORS` - Web server
- `Pillow` - Image processing
- `luma.oled` and `luma.core` - Display drivers

### 4. Start the Server

```powershell
# Still in the virtual environment
python -m kitchenradio.web.kitchen_radio_web
```

### 5. Test It Works

Open in browser:
- **Health check**: http://127.0.0.1:5001/api/health
- **Display image**: http://127.0.0.1:5001/api/display/image
- **Status**: http://127.0.0.1:5001/api/status

### 6. Stop the Server

Press `Ctrl+C` in the terminal

### 7. Deactivate Virtual Environment (When Done)

```powershell
deactivate
```

## Future Usage

Every time you want to run the server:

```powershell
# 1. Navigate to project
cd "c:\Users\ID980331\OneDrive - Proximus\Personal\Home\KitchenRadio"

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Run server
python -m kitchenradio.web.kitchen_radio_web

# 4. When done, deactivate
deactivate
```

## Troubleshooting

### "cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "No module named 'mpd'"

**Solution:** Make sure virtual environment is activated (you see `(venv)` in prompt) and run:
```powershell
pip install python-mpd2
```

### "Address already in use"

**Solution:** Port 5001 is busy, edit the script to use different port or kill the process using port 5001

### Virtual environment already exists

**Solution:** Delete the `venv` folder and recreate:
```powershell
Remove-Item -Recurse -Force venv
python -m venv venv
```

## Why Virtual Environment?

✅ **Isolated**: Doesn't affect system Python
✅ **Clean**: Easy to delete and recreate
✅ **Portable**: Works on any system
✅ **Safe**: Avoids "externally managed environment" errors
✅ **Best Practice**: Industry standard for Python projects

## Alternative: Without Virtual Environment (Not Recommended)

If you really want to install globally:

```powershell
pip install -r requirements.txt --user
```

This installs to your user directory instead of system-wide.

## Summary

**Best approach:**
1. Create venv: `python -m venv venv`
2. Activate: `.\venv\Scripts\Activate.ps1`
3. Install: `pip install -r requirements.txt`
4. Run: `python -m kitchenradio.web.kitchen_radio_web`

That's it! 🚀
