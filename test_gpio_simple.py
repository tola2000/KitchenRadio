#!/usr/bin/env python3
"""
Simple GPIO pin test - directly toggle pin 26 on/off
"""

import time
import sys

print("=" * 80)
print("Simple GPIO Pin 26 Test")
print("=" * 80)
print()

# Test RPi.GPIO
try:
    import RPi.GPIO as GPIO
    print("✅ RPi.GPIO imported successfully")
    
    pin = 26
    print(f"\nTesting GPIO pin {pin}...")
    print(f"This pin should control your amplifier relay")
    print()
    
    # Check current GPIO mode
    current_mode = GPIO.getmode()
    if current_mode is None:
        print("📋 GPIO mode not set, will set to BCM")
        GPIO.setmode(GPIO.BCM)
        print("✅ GPIO mode set to BCM")
    elif current_mode == GPIO.BCM:
        print("✅ GPIO already in BCM mode")
    elif current_mode == GPIO.BOARD:
        print("⚠️  GPIO in BOARD mode, changing to BCM")
        GPIO.cleanup()  # Clean up first
        GPIO.setmode(GPIO.BCM)
        print("✅ GPIO mode set to BCM")
    else:
        print(f"⚠️  GPIO in unknown mode ({current_mode}), setting to BCM")
        GPIO.setmode(GPIO.BCM)
        print("✅ GPIO mode set to BCM")
    
    # Setup pin with initial state
    print(f"\nConfiguring pin {pin}...")
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    print(f"✅ Pin {pin} configured as OUTPUT with initial state LOW")
    
    # Verify initial state
    initial_state = GPIO.input(pin)
    print(f"📊 Verified initial state: {'HIGH' if initial_state else 'LOW'}")
    
    print()
    print("Starting toggle sequence...")
    print("Watch your relay - it should click on/off")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        count = 0
        while True:
            count += 1
            
            # Turn ON
            print(f"[{count}] Setting pin HIGH (relay ON)...")
            GPIO.output(pin, GPIO.HIGH)
            actual = GPIO.input(pin)
            print(f"    📊 Verified state: {'HIGH' if actual else 'LOW'}")
            time.sleep(3)
            
            # Turn OFF
            print(f"[{count}] Setting pin LOW (relay OFF)...")
            GPIO.output(pin, GPIO.LOW)
            actual = GPIO.input(pin)
            print(f"    📊 Verified state: {'HIGH' if actual else 'LOW'}")
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test stopped by user")
    
    # Cleanup
    print("\nCleaning up...")
    GPIO.output(pin, GPIO.LOW)  # Ensure relay is OFF
    GPIO.cleanup(pin)
    print("✅ Cleanup complete")
    
except ImportError as e:
    print(f"❌ Failed to import RPi.GPIO: {e}")
    print("\nTrying gpiozero...")
    
    try:
        from gpiozero import OutputDevice
        print("✅ gpiozero imported successfully")
        
        pin = 26
        print(f"\nTesting GPIO pin {pin} with gpiozero...")
        print(f"This pin should control your amplifier relay")
        print()
        
        # Setup
        relay = OutputDevice(pin, active_high=True, initial_value=False)
        print(f"✅ Pin {pin} configured as OUTPUT (initially OFF)")
        print()
        
        print("Starting toggle sequence...")
        print("Watch your relay - it should click on/off")
        print("Press Ctrl+C to stop")
        print()
        
        try:
            count = 0
            while True:
                count += 1
                
                # Turn ON
                print(f"[{count}] Turning relay ON...")
                relay.on()
                time.sleep(3)
                
                # Turn OFF
                print(f"[{count}] Turning relay OFF...")
                relay.off()
                time.sleep(3)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Test stopped by user")
        
        # Cleanup
        print("\nCleaning up...")
        relay.off()  # Ensure relay is OFF
        relay.close()
        print("✅ Cleanup complete")
        
    except ImportError as e2:
        print(f"❌ Failed to import gpiozero: {e2}")
        print("\n⚠️  No GPIO libraries available!")
        print("Install with: sudo apt-get install python3-rpi.gpio")
        print("          or: pip3 install gpiozero")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ Error during test: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to cleanup on error
    try:
        if 'GPIO' in dir():
            GPIO.cleanup(26)
    except:
        pass
    
    sys.exit(1)

print("\n" + "=" * 80)
print("Test completed successfully")
print("=" * 80)
