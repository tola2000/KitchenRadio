# KitchenRadio Raspberry Pi Hardware Setup

## Overview

This guide shows how to set up the physical KitchenRadio interface on a Raspberry Pi with real buttons and an OLED display.

## Hardware Requirements

### Components
- Raspberry Pi 4B (or Pi 3B+)
- MicroSD card (32GB recommended)
- I2C OLED Display (SSD1306 128x64 recommended)
- 17 Push buttons (momentary, normally open)
- Pull-up resistors (10kΩ) - optional if using internal pull-ups
- Breadboard or PCB for connections
- Jumper wires
- Case/enclosure (optional)

### Recommended OLED Displays
- **SSD1306 128x64** - Most common, good size for radio interface
- **SSD1322 256x64** - Larger, more text space
- **SSD1327 128x128** - Square format

## Raspberry Pi Setup

### 1. OS Installation
```bash
# Flash Raspberry Pi OS Lite to SD card
# Enable SSH and I2C in raspi-config
sudo raspi-config
```

### 2. Enable I2C
```bash
# Enable I2C interface
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable

# Verify I2C is working
sudo i2cdetect -y 1
# Should show devices on the I2C bus
```

### 3. Install Python Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv git i2c-tools

# Install fonts for display
sudo apt install -y fonts-dejavu-core fonts-dejavu-extra

# Clone KitchenRadio
git clone <repository-url>
cd KitchenRadio

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install hardware dependencies
pip install -r requirements-hardware.txt
pip install -r requirements.txt
```

## Hardware Connections

### GPIO Pin Mapping (BCM Numbering)

#### Source Buttons (Top Row)
```
GPIO 2  -> MPD Source Button
GPIO 3  -> Spotify Source Button  
GPIO 4  -> OFF Button
```

#### Menu Buttons (Around Display)
```
GPIO 5  -> Menu UP Button
GPIO 6  -> Menu DOWN Button
GPIO 7  -> Menu TOGGLE Button
GPIO 8  -> Menu SET Button
GPIO 9  -> Menu OK Button
GPIO 10 -> Menu EXIT Button
```

#### Transport Controls (Middle)
```
GPIO 11 -> Previous Track Button
GPIO 12 -> Play/Pause Button
GPIO 13 -> Stop Button
GPIO 14 -> Next Track Button
```

#### Volume Controls (Bottom)
```
GPIO 15 -> Volume DOWN Button
GPIO 16 -> Volume UP Button
```

### I2C Display Connection
```
VCC -> 3.3V (Pin 1)
GND -> Ground (Pin 6)
SDA -> GPIO 2 (Pin 3) - I2C Data
SCL -> GPIO 3 (Pin 5) - I2C Clock
```

### Button Wiring
Each button should be wired as follows:
```
Button Terminal 1 -> GPIO Pin
Button Terminal 2 -> Ground

Note: Internal pull-up resistors are used, 
so external pull-ups are not required.
```

## Physical Layout

```
┌─────────────────────────────────────────┐
│  [MPD]    [Spotify]    [OFF]           │  <- Source Row
│                                         │
│ [UP ]                            [SET ] │
│ [MENU]     ┌─────────────┐      [OK  ] │  <- Menu + Display  
│ [DOWN]     │    OLED     │      [EXIT] │
│            │   Display   │             │
│            └─────────────┘             │
│                                         │
│     [◄◄]   [►/❚❚]  [■]    [►►]        │  <- Transport
│                                         │
│     [VOL-]              [VOL+]         │  <- Volume
└─────────────────────────────────────────┘
```

## Software Configuration

### 1. Test Hardware Controllers
```bash
# Test the hardware controllers
python test_hardware_controllers.py

# Should show:
# ✅ Display controller test
# ✅ Button controller test  
# ✅ Hardware integration info
```

### 2. Run with Hardware Integration
```python
# Example integration in your main script
from kitchenradio.radio.kitchen_radio import KitchenRadio
from kitchenradio.radio.hardware import HardwareIntegration

# Create radio daemon
radio = KitchenRadio()
if radio.start():
    print("KitchenRadio daemon started")
    
    # Add hardware integration
    hardware = HardwareIntegration(radio)
    
    if hardware.initialize():
        print("Physical interface active!")
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            hardware.cleanup()
            radio.stop()
```

### 3. Custom Pin Mapping
```python
# If you need different GPIO pins
from kitchenradio.radio.hardware import ButtonType

custom_pins = {
    ButtonType.SOURCE_MPD: 18,      # Use GPIO 18 instead of 2
    ButtonType.SOURCE_SPOTIFY: 19,  # Use GPIO 19 instead of 3
    # ... map other buttons as needed
}

hardware = HardwareIntegration(
    radio, 
    button_pin_mapping=custom_pins
)
```

### 4. Different Display Types
```python
from kitchenradio.radio.hardware import DisplayType

# For different display sizes/types
hardware = HardwareIntegration(
    radio,
    display_type=DisplayType.SSD1322_256x64,  # Larger display
    i2c_address=0x3D  # Some displays use 0x3D instead of 0x3C
)
```

## Troubleshooting

### Display Issues
```bash
# Check if display is detected
sudo i2cdetect -y 1
# Should show device at 0x3C or 0x3D

# Test with simple luma example
python3 -c "
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas

device = ssd1306(i2c(port=1, address=0x3C))
with canvas(device) as draw:
    draw.text((0, 0), 'Hello World!', fill=255)
"
```

### Button Issues
```bash
# Test GPIO pins individually
python3 -c "
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print('Press button on GPIO 2...')
while True:
    if GPIO.input(2) == GPIO.LOW:
        print('Button pressed!')
        time.sleep(0.5)
    time.sleep(0.1)
"
```

### Permission Issues
```bash
# Add user to required groups
sudo usermod -a -G i2c,spi,gpio $USER

# Reboot to apply group changes
sudo reboot
```

## Systemd Service

Create a systemd service to start KitchenRadio automatically:

```bash
# Create service file
sudo nano /etc/systemd/system/kitchenradio.service
```

```ini
[Unit]
Description=KitchenRadio Physical Interface
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/KitchenRadio
Environment=PATH=/home/pi/KitchenRadio/venv/bin
ExecStart=/home/pi/KitchenRadio/venv/bin/python main_with_hardware.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable kitchenradio.service
sudo systemctl start kitchenradio.service

# Check status
sudo systemctl status kitchenradio.service
```

## Security Notes

- Run KitchenRadio as non-root user (pi)
- Use internal pull-up resistors to prevent floating inputs
- Add debouncing in software (already implemented)
- Consider adding external pull-up resistors for noisy environments

## Performance Tips

- Use Raspberry Pi 4 for better performance
- Use fast SD card (Class 10 or better)
- Consider running from USB drive for better I/O
- Adjust display refresh rate if needed (default: 10 Hz)

## Case Design

Consider 3D printing or building a custom case:
- Ventilation for Raspberry Pi cooling
- Easy access to buttons
- Proper viewing angle for display
- Cable management
- Mounting options

The physical interface creates an authentic radio experience with tactile feedback and a real OLED display showing track information and menus.
