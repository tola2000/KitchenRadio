import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
import time

# ------------------------------
# I2C setup
# ------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x27)  # use your detected address

# ------------------------------
# Configure GPA0 as input with internal pull-up
# ------------------------------
button_pin = mcp.get_pin(0)
button_pin.switch_to_input(pullup=True)

# ------------------------------
# Main loop: detect button press
# ------------------------------
try:
    print("Monitoring Button 0 (GPA0)... Press to test.")
    while True:
        if not button_pin.value:  # active LOW when pressed
            print("Button 0 pressed!")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting...")
