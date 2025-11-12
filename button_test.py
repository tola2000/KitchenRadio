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

last_state = True   # button not pressed (HIGH)
debounce_time = 0.2  # 200 ms
last_time = time.time()

try:
    print("Monitoring Button 0 (GPA0)... Press to test.")
    while True:
        current_state = button_pin.value  # True = not pressed, False = pressed
        current_time = time.time()

        if current_state != last_state:
            # State changed, check debounce
            if (current_time - last_time) >= debounce_time:
                last_time = current_time
                last_state = current_state
                if not current_state:  # pressed
                    print("Button 0 pressed!")
        time.sleep(0.01)
except KeyboardInterrupt:
    print("Exiting...")
