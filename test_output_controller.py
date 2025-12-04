#!/usr/bin/env python3
"""
Test script for OutputController GPIO functionality.

This script tests the amplifier relay control by simulating power on/off events.
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_gpio_import():
    """Test if GPIO libraries are available."""
    logger.info("=" * 80)
    logger.info("Testing GPIO Library Availability")
    logger.info("=" * 80)
    
    try:
        import RPi.GPIO as GPIO
        logger.info("✅ RPi.GPIO is available")
        return 'RPi.GPIO'
    except ImportError:
        logger.info("❌ RPi.GPIO not available")
    
    try:
        from gpiozero import OutputDevice
        logger.info("✅ gpiozero is available")
        return 'gpiozero'
    except ImportError:
        logger.info("❌ gpiozero not available")
    
    logger.warning("⚠️  No GPIO libraries available - will run in simulation mode")
    return None


def test_output_controller_direct():
    """Test OutputController with direct GPIO control."""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Direct GPIO Control (OutputController)")
    logger.info("=" * 80)
    
    # Check GPIO availability first
    gpio_lib = test_gpio_import()
    
    # Import after checking
    from kitchenradio.interfaces.hardware.output_controller import OutputController
    
    # Create a mock source controller
    class MockSourceController:
        def __init__(self):
            self.powered_on = False
            self._callbacks = {}
        
        def add_callback(self, event_name, callback):
            if event_name not in self._callbacks:
                self._callbacks[event_name] = []
            self._callbacks[event_name].append(callback)
            logger.info(f"Registered callback for: {event_name}")
        
        def trigger_power_change(self, powered_on):
            """Manually trigger power change event."""
            logger.info(f"\n📢 Triggering power change: {'ON' if powered_on else 'OFF'}")
            self.powered_on = powered_on
            if 'client_changed' in self._callbacks:
                for callback in self._callbacks['client_changed']:
                    callback(event='power_changed', powered_on=powered_on)
    
    # Create mock source controller
    mock_source = MockSourceController()
    
    # Create OutputController
    logger.info("\nCreating OutputController...")
    output_controller = OutputController(
        source_controller=mock_source,
        amplifier_pin=26,
        use_hardware=True,  # Try to use hardware
        active_high=True,
        power_on_delay=0.0,
        power_off_delay=0.0
    )
    
    # Initialize
    if not output_controller.initialize():
        logger.error("❌ Failed to initialize OutputController")
        return False
    
    logger.info("✅ OutputController initialized")
    
    # Test sequence
    logger.info("\n" + "-" * 80)
    logger.info("Starting Test Sequence")
    logger.info("-" * 80)
    
    try:
        # Test 1: Power ON
        logger.info("\n[Test 1] Power ON")
        mock_source.trigger_power_change(True)
        time.sleep(2)
        
        # Test 2: Power OFF
        logger.info("\n[Test 2] Power OFF")
        mock_source.trigger_power_change(False)
        time.sleep(2)
        
        # Test 3: Power ON again
        logger.info("\n[Test 3] Power ON again")
        mock_source.trigger_power_change(True)
        time.sleep(2)
        
        # Test 4: Power OFF again
        logger.info("\n[Test 4] Power OFF again")
        mock_source.trigger_power_change(False)
        time.sleep(2)
        
        logger.info("\n✅ All tests completed")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user")
    finally:
        # Cleanup
        logger.info("\nCleaning up...")
        output_controller.cleanup()
    
    return True


def test_raw_gpio():
    """Test raw GPIO control without OutputController."""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Raw GPIO Control")
    logger.info("=" * 80)
    
    gpio_lib = test_gpio_import()
    
    if gpio_lib is None:
        logger.error("❌ Cannot test raw GPIO - no libraries available")
        return False
    
    pin = 26
    
    try:
        if gpio_lib == 'RPi.GPIO':
            import RPi.GPIO as GPIO
            
            logger.info(f"\nSetting up GPIO pin {pin} with RPi.GPIO...")
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT)
            
            # Test sequence
            logger.info("\n[Test 1] Set pin HIGH")
            GPIO.output(pin, GPIO.HIGH)
            logger.info(f"✅ Pin {pin} set to HIGH")
            time.sleep(2)
            
            logger.info("\n[Test 2] Set pin LOW")
            GPIO.output(pin, GPIO.LOW)
            logger.info(f"✅ Pin {pin} set to LOW")
            time.sleep(2)
            
            logger.info("\n[Test 3] Set pin HIGH again")
            GPIO.output(pin, GPIO.HIGH)
            logger.info(f"✅ Pin {pin} set to HIGH")
            time.sleep(2)
            
            logger.info("\n[Test 4] Set pin LOW again")
            GPIO.output(pin, GPIO.LOW)
            logger.info(f"✅ Pin {pin} set to LOW")
            time.sleep(2)
            
            # Cleanup
            GPIO.cleanup(pin)
            logger.info(f"\n✅ GPIO pin {pin} cleaned up")
            
        elif gpio_lib == 'gpiozero':
            from gpiozero import OutputDevice
            
            logger.info(f"\nSetting up GPIO pin {pin} with gpiozero...")
            device = OutputDevice(pin, active_high=True, initial_value=False)
            
            # Test sequence
            logger.info("\n[Test 1] Turn ON (HIGH)")
            device.on()
            logger.info(f"✅ Pin {pin} turned ON (HIGH)")
            time.sleep(2)
            
            logger.info("\n[Test 2] Turn OFF (LOW)")
            device.off()
            logger.info(f"✅ Pin {pin} turned OFF (LOW)")
            time.sleep(2)
            
            logger.info("\n[Test 3] Turn ON again")
            device.on()
            logger.info(f"✅ Pin {pin} turned ON (HIGH)")
            time.sleep(2)
            
            logger.info("\n[Test 4] Turn OFF again")
            device.off()
            logger.info(f"✅ Pin {pin} turned OFF (LOW)")
            time.sleep(2)
            
            # Cleanup
            device.close()
            logger.info(f"\n✅ GPIO pin {pin} cleaned up")
        
        logger.info("\n✅ Raw GPIO test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Raw GPIO test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    logger.info("=" * 80)
    logger.info("OutputController GPIO Test Suite")
    logger.info("=" * 80)
    
    print("\nChoose test mode:")
    print("1. Test OutputController (recommended)")
    print("2. Test Raw GPIO control")
    print("3. Run both tests")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        test_output_controller_direct()
    elif choice == '2':
        test_raw_gpio()
    elif choice == '3':
        test_output_controller_direct()
        input("\nPress Enter to continue to raw GPIO test...")
        test_raw_gpio()
    else:
        logger.error("Invalid choice")
        return
    
    logger.info("\n" + "=" * 80)
    logger.info("Test completed")
    logger.info("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
