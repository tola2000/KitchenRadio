import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
import time

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x27)

# Configure GPA0 as input with internal pull-up
button_pin = mcp.get_pin(0)
button_pin.switch_to_input(pullup=True)

button_pressed = False
debounce_time = 0.2  # 200 ms debounce
last_press_time = 0

try:
    print("Monitoring Button 0 (GPA0)... Press to test.")
    while True:
        current_time = time.time()
        if not button_pin.value and not button_pressed:
            if current_time - last_press_time > debounce_time:
                print("Button 0 pressed!")
                button_pressed = True
                last_press_time = current_time
        elif button_pin.value and button_pressed:
            button_pressed = False
        time.sleep(0.01)
except KeyboardInterrupt:
    print("Exiting...")
