#!/usr/bin/env python3
"""
Relay type diagnostic - determine if relay is active-HIGH or active-LOW
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
    
    pin = 26
    
    print("=" * 80)
    print("Relay Type Diagnostic Test")
    print("=" * 80)
    print()
    print("This test will help determine if your relay is active-HIGH or active-LOW")
    print()
    
    # Setup
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    
    print(f"Pin {pin} configured as OUTPUT")
    print()
    
    # Test 1: Set LOW
    print("TEST 1: Setting pin to LOW...")
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.5)
    state = GPIO.input(pin)
    print(f"  Pin state verified: {'HIGH' if state else 'LOW'}")
    print(f"  👂 Listen to the relay - is it clicking/energized?")
    input("  Press Enter when ready...")
    relay_on_at_low = input("  Is the relay ON (energized/clicking)? (y/n): ").lower().strip() == 'y'
    print()
    
    # Test 2: Set HIGH
    print("TEST 2: Setting pin to HIGH...")
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.5)
    state = GPIO.input(pin)
    print(f"  Pin state verified: {'HIGH' if state else 'LOW'}")
    print(f"  👂 Listen to the relay - is it clicking/energized?")
    input("  Press Enter when ready...")
    relay_on_at_high = input("  Is the relay ON (energized/clicking)? (y/n): ").lower().strip() == 'y'
    print()
    
    # Cleanup
    GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup(pin)
    
    # Analysis
    print("=" * 80)
    print("RESULTS:")
    print("=" * 80)
    
    if relay_on_at_high and not relay_on_at_low:
        print("✅ Your relay is ACTIVE-HIGH (normal logic)")
        print("   - Pin HIGH = Relay ON")
        print("   - Pin LOW = Relay OFF")
        print()
        print("Configuration needed:")
        print("   AMPLIFIER_ACTIVE_HIGH = True")
        
    elif relay_on_at_low and not relay_on_at_high:
        print("✅ Your relay is ACTIVE-LOW (inverted logic)")
        print("   - Pin LOW = Relay ON")
        print("   - Pin HIGH = Relay OFF")
        print()
        print("Configuration needed:")
        print("   AMPLIFIER_ACTIVE_HIGH = False")
        
    elif relay_on_at_high and relay_on_at_low:
        print("⚠️  Relay seems to be ON in both states - this is unusual")
        print("   Check your wiring and relay connections")
        
    else:
        print("⚠️  Relay seems to be OFF in both states")
        print("   Possible issues:")
        print("   - Relay not connected to pin 26")
        print("   - Relay not powered")
        print("   - Wrong GPIO pin number")
    
    print("=" * 80)
    
except ImportError:
    print("❌ RPi.GPIO not available")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    try:
        GPIO.cleanup(26)
    except:
        pass
    sys.exit(1)
