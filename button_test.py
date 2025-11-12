import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
import time

i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x27)

button_pin = mcp.get_pin(0)
button_pin.switch_to_input(pullup=True)

button_was_pressed = False

try:
    print("Monitoring Button 0 (GPA0)... Press to test.")
    while True:
        if not button_pin.value and not button_was_pressed:
            print("Button 0 pressed!")
            button_was_pressed = True
        elif button_pin.value and button_was_pressed:
            # button released
            button_was_pressed = False
        time.sleep(0.05)
except KeyboardInterrupt:
    print("Exiting...")
