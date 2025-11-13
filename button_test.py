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

# Debounce settings
debounce_time = 0.05  # 50 ms
last_state = button_pin.value
pending_state = None
pending_since = None

print("Button test started. Press Ctrl+C to exit.")
print(f"Debounce time: {debounce_time*1000}ms\n")

try:
    while True:
        current_state = button_pin.value
        current_time = time.time()

        # Detect state change
        if current_state != last_state:
            # New state change - start debounce timer
            if pending_state is None:
                pending_state = current_state
                pending_since = current_time
            
            # Check if state has been stable long enough
            if pending_state == current_state and (current_time - pending_since) >= debounce_time:
                # Accept the change
                last_state = pending_state
                pending_state = None
                pending_since = None
                
                # Log the event
                if not last_state:  # Button pressed (LOW)
                    print("Button PRESSED")
                else:  # Button released (HIGH)
                    print("Button RELEASED")
        else:
            # State returned to last_state - cancel pending change
            if pending_state is not None:
                pending_state = None
                pending_since = None
        
        time.sleep(0.01)
        
except KeyboardInterrupt:
    print("\nExiting...")
