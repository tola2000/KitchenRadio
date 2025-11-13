import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
import time

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x27)

# Configure GPA0 as input with internal pull-up
# Hardware connection: Button connects GPA0 to GND
# - Not pressed: Pin pulled HIGH (True) by internal resistor
# - Pressed: Pin connected to GND → LOW (False)
button_pin = mcp.get_pin(0)
from digitalio import Pull
button_pin.switch_to_input(pull=Pull.UP)  # Enable pull-up resistor
print(f"Pin configured with pull: {button_pin.pull}")
print("Hardware: Button should connect GPA0 to GND")

# Verify pull-up is enabled by reading GPPU register
# GPPU register address is 0x0C for port A
gppu_value = mcp._read_u8(0x0C)
print(f"GPPU register (Port A): 0x{gppu_value:02X} (bit 0 should be 1 for pull-up)")

# Debounce settings
debounce_time = 0.05  # 50 ms
last_state = button_pin.value
pending_state = None
pending_since = None

print("Button test started. Press Ctrl+C to exit.")
print(f"Debounce time: {debounce_time*1000}ms")
print(f"Initial state: {last_state} (should be True/HIGH with pull-up)\n")

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
                print(f"[DEBUG] New change detected: {last_state} -> {current_state}, starting timer")
            
            # Check if state has been stable long enough
            if pending_state == current_state and (current_time - pending_since) >= debounce_time:
                # Accept the change
                print(f"[DEBUG] Debounce passed, accepting change: {last_state} -> {current_state}")
                last_state = pending_state
                pending_state = None
                pending_since = None
                
                # Log the event
                if not last_state:  # Button pressed (LOW)
                    print(">>> Button PRESSED\n")
                else:  # Button released (HIGH)
                    print(">>> Button RELEASED\n")
        else:
            # State returned to last_state - cancel pending change
            if pending_state is not None:
                print(f"[DEBUG] Bounce detected: state returned to {current_state}")
                pending_state = None
                pending_since = None
        
        time.sleep(0.01)
        
except KeyboardInterrupt:
    print("\nExiting...")
