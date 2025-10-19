#!/usr/bin/env python3
"""
Test script to verify MPD client thread safety
"""

import sys
import os
import threading
import time
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from env_config import get_project_config
    config = get_project_config()
    
    if config and 'PYTHON_PATHS' in config:
        for path in config['PYTHON_PATHS']:
            if path not in sys.path:
                sys.path.insert(0, path)
except Exception as e:
    print(f"Warning: Could not load env config: {e}")

try:
    from kitchenradio.mpd.client import KitchenRadioClient
    
    def test_concurrent_access(client, thread_id, num_operations=10):
        """Test concurrent access to MPD client"""
        print(f"Thread {thread_id}: Starting {num_operations} operations")
        
        for i in range(num_operations):
            try:
                # Test various operations
                status = client.get_status()
                song = client.get_current_song()
                playlists = client.get_all_playlists()
                volume = client.get_volume()
                
                print(f"Thread {thread_id}: Operation {i+1} completed - Status: {bool(status)}, Song: {bool(song)}, Playlists: {len(playlists)}, Volume: {volume}")
                
                # Small delay to allow other threads to run
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Thread {thread_id}: Error in operation {i+1}: {e}")
        
        print(f"Thread {thread_id}: Completed all operations")
    
    print("Testing MPD client thread safety...")
    
    # Create client
    client = KitchenRadioClient()
    
    if client.connect():
        print("✓ Connected to MPD")
        
        # Create multiple threads
        threads = []
        num_threads = 5
        
        print(f"Starting {num_threads} concurrent threads...")
        
        for i in range(num_threads):
            thread = threading.Thread(
                target=test_concurrent_access,
                args=(client, i+1, 5)  # 5 operations per thread
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        print("✓ All threads completed successfully")
        
        client.disconnect()
        print("✓ Thread safety test completed")
        
    else:
        print("✗ Could not connect to MPD")
        print("Make sure MPD is running and accessible")
        
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure all dependencies are installed")
except Exception as e:
    print(f"✗ Error: {e}")
