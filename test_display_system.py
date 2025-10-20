#!/usr/bin/env python3
"""
Test Class for Display Formatter and Emulator Interface

Tests the display system components:
- EmulatorDisplayInterface (BMP image storage)
- DisplayFormatter (text and graphics formatting)
- DisplayController (integration)
"""

import unittest
import logging
import time
import io
from pathlib import Path
from typing import Dict, Any

# Import the components to test
from kitchenradio.web.display_interface_emulator import EmulatorDisplayInterface
from kitchenradio.radio.hardware.display_formatter import DisplayFormatter
from kitchenradio.radio.hardware.display_controller import DisplayController

# Setup logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDisplaySystem(unittest.TestCase):
    """
    Test class for the display system components.
    
    Tests:
    - Display emulator interface functionality
    - Display formatter text and graphics rendering
    - Integration between components
    - BMP image generation and retrieval
    """
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        logger.info("Setting up test fixtures...")
        
        # Create display emulator
        self.emulator = EmulatorDisplayInterface()
        self.assertTrue(self.emulator.initialize(), "Emulator should initialize successfully")
        
        # Create display formatter
        self.formatter = DisplayFormatter()
        
        # Create display controller with emulator
        self.controller = DisplayController(i2c_interface=self.emulator)
        
        logger.info("Test fixtures set up successfully")
    
    def tearDown(self):
        """Clean up after each test method."""
        logger.info("Cleaning up test fixtures...")
        
        if hasattr(self, 'emulator'):
            self.emulator.cleanup()
        
        if hasattr(self, 'controller'):
            self.controller.cleanup()
        
        logger.info("Test fixtures cleaned up")
    
    def test_emulator_initialization(self):
        """Test emulator initialization and basic properties."""
        logger.info("Testing emulator initialization...")
        
        # Test basic properties
        self.assertEqual(self.emulator.width, 256, "Width should be 256")
        self.assertEqual(self.emulator.height, 64, "Height should be 64")
        self.assertEqual(self.emulator.i2c_address, 0x3C, "I2C address should be 0x3C")
        
        # Test display info
        info = self.emulator.get_display_info()
        self.assertIsInstance(info, dict, "Display info should be a dictionary")
        self.assertEqual(info['width'], 256, "Info width should be 256")
        self.assertEqual(info['height'], 64, "Info height should be 64")
        self.assertTrue(info['emulation_mode'], "Should be in emulation mode")
        
        logger.info("✅ Emulator initialization test passed")
    
    def test_emulator_clear_and_image_generation(self):
        """Test display clearing and BMP image generation."""
        logger.info("Testing emulator clear and image generation...")
        
        # Test clear operation
        self.emulator.clear()
        
        # Check that BMP data is generated
        bmp_data = self.emulator.getDisplayImage()
        self.assertIsNotNone(bmp_data, "BMP data should be generated after clear")
        self.assertIsInstance(bmp_data, bytes, "BMP data should be bytes")
        self.assertGreater(len(bmp_data), 100, "BMP data should have reasonable size")
        
        # Check PIL image is available
        pil_image = self.emulator.get_display_image_pil()
        self.assertIsNotNone(pil_image, "PIL image should be available")
        self.assertEqual(pil_image.size, (256, 64), "PIL image should have correct size")
        
        logger.info("✅ Emulator clear and image generation test passed")
    
    def test_emulator_custom_drawing(self):
        """Test custom drawing on the emulator."""
        logger.info("Testing emulator custom drawing...")
        
        # Define a custom drawing function
        def draw_test_content(draw):
            # Draw text
            draw.text((10, 10), "KitchenRadio Test", fill=255)
            draw.text((10, 30), "Display System", fill=255)
            
            # Draw shapes
            draw.rectangle([(5, 5), (250, 60)], outline=255)
            draw.line([(0, 32), (256, 32)], fill=255)
            draw.circle((230, 32), 15, outline=255)
        
        # Render the custom drawing
        result = self.emulator.render_frame(draw_test_content)
        self.assertTrue(result, "Custom drawing should succeed")
        
        # Check that BMP data is updated
        bmp_data = self.emulator.getDisplayImage()
        self.assertIsNotNone(bmp_data, "BMP data should be available after drawing")
        
        # Check that last update time is recent
        info = self.emulator.get_display_info()
        self.assertLess(time.time() - info['last_update'], 2.0, "Last update should be recent")
        
        logger.info("✅ Emulator custom drawing test passed")
    
    def test_formatter_initialization(self):
        """Test display formatter initialization."""
        logger.info("Testing formatter initialization...")
        
        # Test basic properties
        self.assertEqual(self.formatter.width, 256, "Formatter width should be 256")
        self.assertEqual(self.formatter.height, 64, "Formatter height should be 64")
        
        # Test fonts are loaded
        self.assertIsInstance(self.formatter.fonts, dict, "Fonts should be a dictionary")
        self.assertIn('default', self.formatter.fonts, "Default font should be available")
        
        logger.info("✅ Formatter initialization test passed")
    
    def test_formatter_text_rendering(self):
        """Test formatter text rendering functions."""
        logger.info("Testing formatter text rendering...")
        
        # Test simple text display
        draw_func = self.formatter.format_simple_text("Test Message", "Sub Text")
        self.assertIsNotNone(draw_func, "Text formatting should return a function")
        self.assertTrue(callable(draw_func), "Returned value should be callable")
        
        # Test rendering with emulator
        result = self.emulator.render_frame(draw_func)
        self.assertTrue(result, "Text rendering should succeed")
        
        # Check BMP data is generated
        bmp_data = self.emulator.getDisplayImage()
        self.assertIsNotNone(bmp_data, "BMP data should be generated after text rendering")
        
        logger.info("✅ Formatter text rendering test passed")
    
    def test_formatter_status_display(self):
        """Test formatter status display with mock data."""
        logger.info("Testing formatter status display...")
        
        # Create mock status data
        mock_status = {
            'current_source': 'mpd',
            'mpd': {
                'connected': True,
                'state': 'play',
                'volume': 75,
                'current_song': {
                    'title': 'Test Song',
                    'artist': 'Test Artist',
                    'album': 'Test Album'
                }
            },
            'librespot': {
                'connected': False
            }
        }
        
        # Test status formatting
        draw_func = self.formatter.format_status(mock_status)
        self.assertIsNotNone(draw_func, "Status formatting should return a function")
        self.assertTrue(callable(draw_func), "Returned value should be callable")
        
        # Test rendering with emulator
        result = self.emulator.render_frame(draw_func)
        self.assertTrue(result, "Status rendering should succeed")
        
        # Check BMP data is generated
        bmp_data = self.emulator.getDisplayImage()
        self.assertIsNotNone(bmp_data, "BMP data should be generated after status rendering")
        
        logger.info("✅ Formatter status display test passed")
    
    def test_controller_integration(self):
        """Test display controller integration with emulator."""
        logger.info("Testing controller integration...")
        
        # Test controller initialization
        self.assertTrue(self.controller.initialize(), "Controller should initialize successfully")
        
        # Test display update
        result = self.controller.update_display()
        self.assertTrue(result, "Display update should succeed")
        
        # Test status display
        mock_status = {
            'current_source': 'mpd',
            'mpd': {'connected': True, 'state': 'stop'},
            'librespot': {'connected': False}
        }
        
        result = self.controller.show_status(mock_status)
        self.assertTrue(result, "Show status should succeed")
        
        logger.info("✅ Controller integration test passed")
    
    def test_bmp_image_properties(self):
        """Test BMP image properties and format."""
        logger.info("Testing BMP image properties...")
        
        # Render some content
        def draw_test(draw):
            draw.text((50, 20), "BMP Test", fill=255)
            draw.rectangle([(40, 15), (150, 40)], outline=255)
        
        self.emulator.render_frame(draw_test)
        
        # Get BMP data
        bmp_data = self.emulator.getDisplayImage()
        self.assertIsNotNone(bmp_data, "BMP data should exist")
        
        # Check BMP header (first 14 bytes should be BMP signature and header)
        self.assertEqual(bmp_data[:2], b'BM', "Should start with BMP signature")
        
        # Test that we can save the BMP data to a file
        test_file_path = Path("test_display_output.bmp")
        try:
            with open(test_file_path, 'wb') as f:
                f.write(bmp_data)
            
            # Verify file was created and has content
            self.assertTrue(test_file_path.exists(), "BMP file should be created")
            self.assertGreater(test_file_path.stat().st_size, 100, "BMP file should have content")
            
        finally:
            # Clean up test file
            if test_file_path.exists():
                test_file_path.unlink()
        
        logger.info("✅ BMP image properties test passed")
    
    def test_error_handling(self):
        """Test error handling in display components."""
        logger.info("Testing error handling...")
        
        # Test invalid drawing function
        def bad_draw_func(draw):
            raise ValueError("Test error")
        
        # Should handle error gracefully
        result = self.emulator.render_frame(bad_draw_func)
        self.assertFalse(result, "Bad drawing function should return False")
        
        # Emulator should still be functional after error
        def good_draw_func(draw):
            draw.text((10, 10), "Recovery Test", fill=255)
        
        result = self.emulator.render_frame(good_draw_func)
        self.assertTrue(result, "Emulator should recover from errors")
        
        logger.info("✅ Error handling test passed")
    
    def test_performance(self):
        """Test performance of display operations."""
        logger.info("Testing display performance...")
        
        # Define a complex drawing function
        def complex_draw(draw):
            for i in range(10):
                draw.text((10, i * 6), f"Line {i}: Test Performance", fill=255)
            for i in range(0, 256, 20):
                draw.line([(i, 0), (i, 64)], fill=128)
        
        # Measure rendering time
        start_time = time.time()
        for i in range(10):
            result = self.emulator.render_frame(complex_draw)
            self.assertTrue(result, f"Render {i} should succeed")
        end_time = time.time()
        
        # Performance check
        total_time = end_time - start_time
        avg_time = total_time / 10
        
        logger.info(f"Average render time: {avg_time:.3f}s")
        self.assertLess(avg_time, 0.5, "Average render time should be under 0.5 seconds")
        
        logger.info("✅ Performance test passed")


def run_display_tests():
    """Run all display system tests."""
    logger.info("Starting Display System Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDisplaySystem)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        logger.info("🎉 All display system tests passed!")
    else:
        logger.error(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        for failure in result.failures:
            logger.error(f"FAILURE: {failure[0]}")
            logger.error(failure[1])
        
        for error in result.errors:
            logger.error(f"ERROR: {error[0]}")
            logger.error(error[1])
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the tests when script is executed directly
    success = run_display_tests()
    exit(0 if success else 1)
