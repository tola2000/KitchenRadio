import time
import logging
import spidev
import RPi.GPIO as GPIO

# -------------------------------------------------------------
# Logging
# -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logging.info("Starting raw SSD1322 SPI test")

# -------------------------------------------------------------
# GPIO setup for RES# and D/C#
# -------------------------------------------------------------
RES_PIN = 24  # Connect to SSD1322 RES#
DC_PIN  = 25  # Connect to SSD1322 D/C#

GPIO.setmode(GPIO.BCM)
GPIO.setup(RES_PIN, GPIO.OUT)
GPIO.setup(DC_PIN, GPIO.OUT)

# -------------------------------------------------------------
# Reset the display manually
# -------------------------------------------------------------
logging.info("Toggling RESET pin")
GPIO.output(RES_PIN, GPIO.LOW)
time.sleep(0.05)  # 50 ms
GPIO.output(RES_PIN, GPIO.HIGH)
time.sleep(0.05)  # 50 ms

# -------------------------------------------------------------
# SPI setup
# -------------------------------------------------------------
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI0, CE0
spi.max_speed_hz = 4000000  # 4 MHz
spi.mode = 0b00

logging.info("SPI interface initialized")

# -------------------------------------------------------------
# Helper function to send commands/data
# -------------------------------------------------------------
def send_command(cmd):
    GPIO.output(DC_PIN, GPIO.LOW)  # Command mode
    spi.xfer([cmd])

def send_data(data):
    GPIO.output(DC_PIN, GPIO.HIGH)  # Data mode
    if isinstance(data, int):
        spi.xfer([data])
    else:
        spi.xfer(data)

# -------------------------------------------------------------
# Test sequence
# -------------------------------------------------------------
try:
    logging.info("Turning display OFF")
    send_command(0xAE)  # Display OFF
    time.sleep(1)

    logging.info("Turning display ON")
    send_command(0xAF)  # Display ON
    time.sleep(1)

    logging.info("Filling display with 0xFF (all pixels)")
    send_command(0x15)  # Set column start/end
    send_data([0x00, 0x7F])  # 0–127 for 256 width (4-bit per pixel)
    send_command(0x75)  # Set row start/end
    send_data([0x00, 0x3F])  # 0–63

    # Fill RAM with 0xFF (white)
    GPIO.output(DC_PIN, GPIO.HIGH)
    for _ in range(256 * 64 // 2):  # 4-bit per pixel, 2 pixels per byte
        spi.xfer([0xFF])
    logging.info("Display should now be filled")

    time.sleep(5)

    logging.info("Clearing display")
    GPIO.output(DC_PIN, GPIO.HIGH)
    for _ in range(256 * 64 // 2):
        spi.xfer([0x00])

    logging.info("Test sequence completed successfully")

except Exception as e:
    logging.error(f"Error during test: {e}")

finally:
    spi.close()
    GPIO.cleanup()
    logging.info("Cleaned up SPI and GPIO")
