#!/usr/bin/env python3
"""
MoOde Audio Endpoint Discovery Script

This script tries to discover what API endpoints are available on a MoOde server.
"""

import requests
import sys
from urllib.parse import urljoin


def discover_moode_endpoints(host="localhost", port=80):
    """Discover available MoOde endpoints."""
    base_url = f"http://{host}:{port}"
    session = requests.Session()
    
    print(f"🔍 Discovering MoOde endpoints on {base_url}")
    print("=" * 50)
    
    # Common MoOde/MPD endpoints to test
    test_endpoints = [
        "/",
        "/index.php",
        "/command/",
        "/engine-mpd.php",
        "/engine-cmd.php", 
        "/api/",
        "/api/volume",
        "/vol.php",
        "/cmd.php",
        "/sysinfo.php",
        "/currentsong.php",
        "/status.php",
        "/player.php",
        "/mpc.php",
        "/mpd.php",
    ]
    
    available_endpoints = []
    
    for endpoint in test_endpoints:
        url = urljoin(base_url, endpoint)
        try:
            response = session.get(url, timeout=5)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {endpoint} - Available (200 OK)")
                available_endpoints.append(endpoint)
            elif status == 404:
                print(f"❌ {endpoint} - Not found (404)")
            elif status == 403:
                print(f"⚠️  {endpoint} - Forbidden (403)")
            elif status == 500:
                print(f"⚠️  {endpoint} - Server error (500)")
            else:
                print(f"❓ {endpoint} - Status {status}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Connection error: {e}")
    
    print(f"\n📋 Summary: Found {len(available_endpoints)} available endpoints")
    
    if available_endpoints:
        print("\n🔍 Testing volume commands on available endpoints...")
        test_volume_commands(session, base_url, available_endpoints)
    
    return available_endpoints


def test_volume_commands(session, base_url, endpoints):
    """Test volume-related commands on discovered endpoints."""
    
    volume_tests = [
        # Correct MoOde format
        {"endpoint": "/command/?status", "method": "GET", "params": None},
        {"endpoint": "/command/?setvol%2050", "method": "GET", "params": None},
        # GET requests with parameters  
        {"endpoint": "/command/", "method": "GET", "params": {"cmd": "status"}},
        {"endpoint": "/command/", "method": "GET", "params": {"cmd": "setvol", "vol": "50"}},
        {"endpoint": "/engine-mpd.php", "method": "POST", "data": {"cmd": "status"}},
        {"endpoint": "/engine-mpd.php", "method": "POST", "data": {"cmd": "setvol 50"}},
        {"endpoint": "/engine-cmd.php", "method": "POST", "data": {"cmd": "setvol 50"}},
        {"endpoint": "/api/volume", "method": "POST", "data": {"volume": 50}},
        {"endpoint": "/vol.php", "method": "POST", "data": {"vol": 50}},
    ]
    
    for test in volume_tests:
        endpoint = test["endpoint"]
        
        # Handle both simple endpoints and full URLs with parameters
        if "?" in endpoint:
            # Full endpoint with parameters (like /command/?setvol%2050)
            base_endpoint = endpoint.split("?")[0]
            if base_endpoint in endpoints or endpoint.startswith("/command/"):
                url = urljoin(base_url, endpoint)
                try:
                    response = session.get(url, timeout=5)
                    print(f"  GET {endpoint}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        content = response.text[:200]  # First 200 chars
                        print(f"    Response: {content}")
                        
                except Exception as e:
                    print(f"  ❌ GET {endpoint}: Error - {e}")
        elif endpoint in endpoints:
            url = urljoin(base_url, endpoint)
            
            try:
                if test["method"] == "GET":
                    response = session.get(url, params=test.get("params"), timeout=5)
                else:
                    response = session.post(url, data=test.get("data"), timeout=5)
                
                print(f"  {test['method']} {endpoint}: Status {response.status_code}")
                
                if response.status_code == 200:
                    content = response.text[:200]  # First 200 chars
                    print(f"    Response: {content}")
                    
            except Exception as e:
                print(f"  ❌ {test['method']} {endpoint}: Error - {e}")


def main():
    """Main discovery function."""
    print("🔍 MoOde Audio Endpoint Discovery")
    print("=" * 35)
    
    # Parse command line arguments
    host = "localhost"
    port = 80
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"❌ Invalid port: {sys.argv[2]}")
            sys.exit(1)
    
    try:
        endpoints = discover_moode_endpoints(host, port)
        
        if not endpoints:
            print(f"\n❌ No endpoints found on {host}:{port}")
            print("This might not be a MoOde Audio server, or it might be unreachable.")
        else:
            print(f"\n✅ Discovery completed! Found {len(endpoints)} endpoints.")
            
    except KeyboardInterrupt:
        print("\n🛑 Discovery interrupted by user")
    except Exception as e:
        print(f"\n❌ Discovery failed: {e}")


if __name__ == "__main__":
    main()
