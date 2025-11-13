import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017
import time

# I2C setup
print("Initializing I2C and MCP23017...")
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x27)
print(f"MCP23017 found at address 0x27")

# Configure GPA0 as input with internal pull-up
button_pin = mcp.get_pin(0)
button_pin.switch_to_input(pullup=True)
print("Button 0 (GPA0) configured as input with pull-up")

last_state = True   # button not pressed (HIGH)
debounce_time = 0.2  # 200 ms
last_change_time = time.time()
event_counter = 0
pending_state = None  # Track state waiting to be accepted
pending_since = None  # When pending state was first detected

print("\n" + "="*60)
print("Button Monitoring Started")
print("="*60)
print("Initial state: HIGH (not pressed)")
print(f"Debounce time: {debounce_time*1000}ms")
print("Monitoring... (Ctrl+C to exit)\n")

try:
    while True:
        current_state = button_pin.value  # True = not pressed (HIGH), False = pressed (LOW)
        current_time = time.time()
        time_since_last_change = current_time - last_change_time

        # Check if we have a new state change
        if current_state != last_state:
            # Is this a new state change or same as pending?
            if pending_state != current_state:
                # NEW state change detected
                event_counter += 1
                state_str = "HIGH (not pressed)" if current_state else "LOW (pressed)"
                old_state_str = "HIGH (not pressed)" if last_state else "LOW (pressed)"
                
                print(f"[{event_counter:04d}] State change detected: {old_state_str} -> {state_str}")
                print(f"       Time since last accepted change: {time_since_last_change*1000:.1f}ms")
                
                # Store as pending
                pending_state = current_state
                pending_since = current_time
                print(f"       ⏱ Starting debounce timer...")
            
            # Check if pending state has been stable long enough
            if pending_state is not None:
                time_pending = current_time - pending_since
                
                if time_pending >= debounce_time:
                    # Debounce passed - accept the change
                    print(f"       ✓ DEBOUNCE PASSED ({time_pending*1000:.1f}ms) - Accepting state change")
                    last_change_time = current_time
                    last_state = pending_state
                    pending_state = None
                    pending_since = None
                    
                    if not last_state:  # pressed (LOW)
                        print(f"       >>> BUTTON 0 PRESSED <<<\n")
                    else:  # released (HIGH)
                        print(f"       >>> BUTTON 0 RELEASED <<<\n")
        else:
            # Current state matches last_state - cancel any pending change
            if pending_state is not None:
                time_pending = current_time - pending_since
                print(f"       ✗ State bounced back before debounce ({time_pending*1000:.1f}ms) - Rejecting change")
                print(f"       State stabilized at: {'HIGH (not pressed)' if current_state else 'LOW (pressed)'}\n")
                pending_state = None
                pending_since = None
        
        time.sleep(0.01)
        
except KeyboardInterrupt:
    print("\n" + "="*60)
    print(f"Exiting... Total events detected: {event_counter}")
    print("="*60)
