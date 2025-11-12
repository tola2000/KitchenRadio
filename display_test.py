from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from luma.core.render import canvas
from PIL import ImageFont, ImageDraw
import time

# --- SPI interface configuration ---
serial = spi(
    port=0,               # SPI0
    device=0,             # CE0 (GPIO8)
    gpio_DC=25,           # D/C# pin (GPIO25)
    gpio_RST=24,          # RESET pin (GPIO24)
    bus_speed_hz=4000000  # 8 MHz, safe starting speed
)

# --- Initialize display ---
device = ssd1322(serial, width=256, height=64)

# --- Test screen ---
with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((10, 10), "SSD1322 TEST", fill="white")
    draw.text((10, 30), "Hello Raspberry Pi!", fill="white")

time.sleep(3)

# --- Moving dot test ---
x = 0
direction = 1
while True:
    with canvas(device) as draw:
        draw.text((10, 10), "Moving dot...", fill="white")
        draw.ellipse((x, 40, x + 6, 46), fill="white")
    x += direction * 5
    if x <= 0 or x >= 250:
        direction *= -1
    time.sleep(0.05)
