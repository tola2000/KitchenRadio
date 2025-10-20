#!/usr/bin/env python3
"""
Test script for Display Image API

Tests the display emulator image retrieval through the web API.
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_display_api(base_url="http://localhost:5100"):
    """Test the display API endpoints"""
    
    print("🧪 Testing Display Image API")
    print("=" * 50)
    
    # Test health check first
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Web server is running: {health}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to web server: {e}")
        print(f"💡 Make sure the web server is running on {base_url}")
        return False
    
    # Test display endpoints
    endpoints = [
        ("/api/display/image", "Display Image Data"),
        ("/api/display/ascii", "Display ASCII Art"),
    ]
    
    for endpoint, description in endpoints:
        print(f"\n🔍 Testing {description}...")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ {description} - Success")
                    
                    if 'image_data' in data:
                        width = data.get('width', 0)
                        height = data.get('height', 0)
                        stats = data.get('statistics', {})
                        print(f"   📐 Dimensions: {width}x{height}")
                        print(f"   📊 On pixels: {stats.get('on_pixels', 0)}/{stats.get('total_pixels', 0)}")
                        print(f"   📈 Fill: {stats.get('fill_percentage', 0):.1f}%")
                        
                        # Show first few rows of image data
                        image_data = data.get('image_data', [])
                        if image_data and len(image_data) > 0:
                            print("   🖼️  First 5 rows:")
                            for i, row in enumerate(image_data[:5]):
                                # Convert pixels to simple representation
                                row_str = ''.join('█' if pixel > 128 else ' ' for pixel in row[:40])
                                print(f"      {row_str}")
                    
                    elif 'ascii_art' in data:
                        ascii_art = data.get('ascii_art', '')
                        print(f"   🎨 ASCII Art:")
                        print(f"      {ascii_art[:200]}...")  # Show first 200 chars
                        
                else:
                    print(f"❌ {description} - API returned success=false")
                    print(f"   Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ {description} - HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {description} - Request failed: {e}")
    
    # Test display control endpoints
    control_tests = [
        ("POST", "/api/display/clear", {}, "Clear Display"),
        ("POST", "/api/display/test", {}, "Test Pattern"),
    ]
    
    for method, endpoint, data, description in control_tests:
        print(f"\n🎮 Testing {description}...")
        try:
            if method == "POST":
                response = requests.post(f"{base_url}{endpoint}", json=data, timeout=10)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ {description} - Success")
                    message = result.get('message', '')
                    if message:
                        print(f"   💬 {message}")
                else:
                    print(f"❌ {description} - Failed")
                    print(f"   Error: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ {description} - HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {description} - Request failed: {e}")
    
    # Final image check after test pattern
    print(f"\n🔍 Final image check after test pattern...")
    try:
        time.sleep(1)  # Wait for test pattern to clear
        response = requests.get(f"{base_url}/api/display/ascii", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                ascii_art = data.get('ascii_art', '')
                print(f"✅ Final ASCII representation:")
                lines = ascii_art.split('\n')
                for line in lines[:10]:  # Show first 10 lines
                    print(f"   {line}")
        
    except Exception as e:
        print(f"❌ Final check failed: {e}")
    
    print(f"\n✅ Display API test completed")
    return True


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Display Image API')
    parser.add_argument('--url', default='http://localhost:5100', 
                       help='Base URL of the web server (default: http://localhost:5100)')
    
    args = parser.parse_args()
    
    print(f"🚀 Testing Display API at: {args.url}")
    print(f"📅 Test started at: {datetime.now()}")
    
    success = test_display_api(args.url)
    
    if success:
        print(f"\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
