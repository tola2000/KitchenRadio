#!/usr/bin/env python3

from kitchenradio.radio.hardware.display_formatter import DisplayFormatter

def test_format_text_return_structure():
    """Test that _format_text returns the expected structure"""
    formatter = DisplayFormatter(width=256, height=64)
    
    # Test with return_info=True
    result = formatter._format_text(
        "This is a test text", 
        100,  # max_width
        formatter.fonts['medium'], 
        0,  # scroll_offset
        'medium',  # font_size
        return_info=True
    )
    
    print("Return info structure:")
    print(f"Type: {type(result)}")
    print(f"Keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
    print(f"Content: {result}")
    
    # Verify it has the expected structure
    if isinstance(result, dict):
        expected_keys = {'displayed', 'truncated', 'original_width', 'max_width', 'scroll_offset', 'font_size'}
        if set(result.keys()) == expected_keys:
            print("✓ Structure matches expected format")
        else:
            print(f"✗ Missing keys: {expected_keys - set(result.keys())}")
            print(f"✗ Extra keys: {set(result.keys()) - expected_keys}")
    else:
        print("✗ Result is not a dictionary")
    
    # Test with return_info=False
    simple_result = formatter._format_text(
        "This is a test text", 
        100,  # max_width
        formatter.fonts['medium'], 
        0,  # scroll_offset
        'medium'  # font_size
    )
    
    print(f"\nSimple result: '{simple_result}' (type: {type(simple_result)})")
    
    if isinstance(simple_result, str):
        print("✓ Simple result is a string as expected")
    else:
        print("✗ Simple result should be a string")

if __name__ == "__main__":
    test_format_text_return_structure()
