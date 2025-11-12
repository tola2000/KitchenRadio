import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
import RPi.GPIO as GPIO
import time

# ------------------------------
# Raspberry Pi GPIO for MCP23017 interrupts (optional)
# ------------------------------
INTA_PIN = 17  # Connect MCP23017 INTA here if you want interrupt detection
GPIO.setmode(GPIO.BCM)
GPIO.setup(INTA_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ------------------------------
# I2C setup
# ------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x27)  # use detected address 0x27

# ------------------------------
# Configure GPA0-GPA7 as inputs with internal pull-ups
# ------------------------------
buttons = []
for i in range(8):
    pin = mcp.get_pin(i)
    pin.switch_to_input(pullup=True)
    buttons.append(pin)

# ------------------------------
# Interrupt callback function (optional)
# ------------------------------
def intA_callback(channel):
    pressed = [i for i, pin in enumerate(buttons) if not pin.value]
    if pressed:
        print("Button(s) pressed (interrupt):", pressed)

GPIO.add_event_detect(INTA_PIN, GPIO.FALLING, callback=intA_callback, bouncetime=200)

# ------------------------------
# Main loop: polling as backup
# ------------------------------
try:
    print("Monitoring buttons on MCP23017 (address 0x27)...")
    while True:
        pressed = [i for i, pin in enumerate(buttons) if not pin.value]
        if pressed:
            print("Button(s) pressed (polled):", pressed)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
