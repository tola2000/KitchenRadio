import time
import logging
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from luma.core.render import canvas
from PIL import ImageFont, ImageDraw

# -------------------------------------------------------------
# Setup logging
# -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

logging.info("Starting SSD1322 OLED test script")

# -------------------------------------------------------------
# SPI configuration
# -------------------------------------------------------------
SPI_BUS_SPEED = 4000000  # 4 MHz — stable default, can raise up to ~10 MHz

logging.info(f"Initializing SPI interface at {SPI_BUS_SPEED / 1e6:.1f} MHz")

serial = spi(
    port=0,               # SPI0
    device=0,             # CE0 (GPIO8)
    gpio_DC=25,           # D/C# pin (GPIO25)
    gpio_RST=24,          # RESET pin (GPIO24)
    bus_speed_hz=SPI_BUS_SPEED
)

# -------------------------------------------------------------
# Initialize SSD1322 display
# -------------------------------------------------------------
try:
    device = ssd1322(serial, width=256, height=64)
    logging.info("SSD1322 display initialized successfully")
except Exception as e:
    logging.error(f"Display initialization failed: {e}")
    raise SystemExit(1)

# -------------------------------------------------------------
# Test pattern 1: Static text
# -------------------------------------------------------------
logging.info("Displaying test text on OLED")
with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((10, 10), "SSD1322 TEST", fill="white")
    draw.text((10, 30), "Hello Raspberry Pi!", fill="white")

time.sleep(3)

# -------------------------------------------------------------
# Test pattern 2: Moving dot animation
# -------------------------------------------------------------
logging.info("Starting moving dot animation (Ctrl+C to exit)")
x = 0
direction = 1

try:
    while True:
        with canvas(device) as draw:
            draw.text((10, 10), "Moving dot...", fill="white")
            draw.ellipse((x, 40, x + 6, 46), fill="white")
        x += direction * 5
        if x <= 0 or x >= 250:
            direction *= -1
        time.sleep(0.05)
except KeyboardInterrupt:
    logging.info("Exiting gracefully after user interrupt")
except Exception as e:
    logging.error(f"Runtime error: {e}")
finally:
    logging.info("Clearing display before exit")
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")
    time.sleep(0.5)
