import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
import time

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
# Main loop: polling
# ------------------------------
try:
    print("Monitoring buttons on MCP23017 (address 0x27)...")
    while True:
        pressed = [i for i, pin in enumerate(buttons) if not pin.value]
        if pressed:
            print("Button(s) pressed:", pressed)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting...")
