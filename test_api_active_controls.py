#!/usr/bin/env python3
"""
Test script for KitchenRadio active source control API endpoints
"""

import sys
import time
import requests
import json
from pathlib import Path

def test_api_endpoints():
    """Test the active source control API endpoints"""
    try:
        # Base URL for the web server
        base_url = "http://localhost:5000"
        
        print("=== Testing KitchenRadio Active Source Control API ===\n")
        
        # Test health check first
        print("1. Testing health endpoint...")
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("   ✓ Web server is running")
            else:
                print(f"   ✗ Health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ✗ Cannot connect to web server: {e}")
            print("   Make sure the web server is running on localhost:5000")
            return False
        
        # Get current status
        print("\n2. Getting current status...")
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   ✓ Status retrieved")
            print(f"   Current source: {status.get('current_source', 'None')}")
            print(f"   Available sources: {status.get('available_sources', [])}")
            
            # If no current source, try to set one
            if not status.get('current_source') and status.get('available_sources'):
                first_source = status['available_sources'][0]
                print(f"\n   Setting source to {first_source}...")
                set_response = requests.post(f"{base_url}/api/source/{first_source}")
                if set_response.status_code == 200:
                    print(f"   ✓ Source set to {first_source}")
                else:
                    print(f"   ✗ Failed to set source: {set_response.json()}")
        else:
            print(f"   ✗ Failed to get status: {response.status_code}")
            return False
        
        # Test control commands
        print("\n3. Testing control commands...")
        commands = ['play', 'pause', 'stop', 'next', 'previous', 'play_pause']
        
        for command in commands:
            print(f"   Testing {command}...")
            try:
                response = requests.post(f"{base_url}/api/control/{command}", timeout=10)
                result = response.json()
                
                if response.status_code == 200 and result.get('success'):
                    print(f"      ✓ {command} successful: {result.get('message', '')}")
                else:
                    print(f"      ✗ {command} failed: {result.get('error', 'Unknown error')}")
                
                # Small delay between commands
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"      ✗ Network error for {command}: {e}")
            except json.JSONDecodeError as e:
                print(f"      ✗ JSON decode error for {command}: {e}")
        
        # Test invalid command
        print("\n4. Testing invalid command...")
        response = requests.post(f"{base_url}/api/control/invalid_command")
        if response.status_code == 400:
            print("   ✓ Invalid command properly rejected")
        else:
            print(f"   ✗ Unexpected response for invalid command: {response.status_code}")
        
        # Test with no active source (if possible)
        print("\n5. Testing with no active source...")
        # First clear the source by setting it to empty (this might not work depending on API)
        # Then try a command
        response = requests.post(f"{base_url}/api/control/play")
        result = response.json()
        if response.status_code == 400 and 'No active source' in result.get('error', ''):
            print("   ✓ No active source properly handled")
        else:
            print("   ℹ️ Active source was available (expected if source is set)")
        
        print("\n✓ All API tests completed")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during API testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("This test requires the KitchenRadio web server to be running.")
    print("Start it with: python web/kitchen_radio_web.py or python debug_flask.py\n")
    
    response = input("Is the web server running? (y/n): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Please start the web server first and then run this test again.")
        return False
    
    return test_api_endpoints()

if __name__ == "__main__":
    success = main()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
