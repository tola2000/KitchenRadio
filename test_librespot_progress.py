#!/usr/bin/env python3
"""
Simple test using existing KitchenRadio librespot client to check seek position updates.
This uses the same client that KitchenRadio uses.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from kitchenradio.librespot import KitchenRadioLibrespotClient
except ImportError as e:
    print(f"ERROR: Could not import KitchenRadioLibrespotClient: {e}")
    print("Make sure you're running this from the KitchenRadio project directory.")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LibrespotProgressTest:
    def __init__(self):
        self.client = KitchenRadioLibrespotClient()
        self.last_position = None
        
    async def test_progress_updates(self):
        """Test librespot progress updates"""
        logger.info("Starting Librespot progress test...")
        logger.info("Play some music on Spotify to see updates.")
        logger.info("Press Ctrl+C to exit.\n")
        
        try:
            # Start the librespot client
            await self.client.start()
            logger.info("Librespot client started successfully")
            
            # Monitor for updates
            while True:
                try:
                    # Get current status
                    status = await self.client.get_status()
                    
                    if status:
                        await self.handle_status_update(status)
                    else:
                        logger.debug("No status received")
                        
                    # Wait a bit before next check
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error getting status: {e}")
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("Test interrupted by user")
        except Exception as e:
            logger.error(f"Test failed: {e}")
        finally:
            try:
                await self.client.stop()
                logger.info("Librespot client stopped")
            except:
                pass
    
    async def handle_status_update(self, status):
        """Handle status updates and show progress info"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Extract key information
        connected = status.get('connected', False)
        state = status.get('state', 'unknown')
        volume = status.get('volume', 0)
        
        # Progress information
        progress_ms = status.get('progress_ms', 0)
        current_track = status.get('current_track', {})
        duration_ms = current_track.get('duration_ms', 0)
        
        # Track information
        track_name = current_track.get('name', 'Unknown')
        artist = current_track.get('artist', 'Unknown')
        
        # Only log if there are meaningful updates
        if not connected:
            logger.info(f"[{timestamp}] Spotify not connected")
            return
            
        if state not in ['playing', 'paused']:
            logger.info(f"[{timestamp}] State: {state}")
            return
            
        # Show progress updates
        if duration_ms > 0:
            progress_pct = (progress_ms / duration_ms) * 100
            progress_time = f"{progress_ms//60000:02d}:{(progress_ms//1000)%60:02d}"
            total_time = f"{duration_ms//60000:02d}:{(duration_ms//1000)%60:02d}"
            
            # Only log if position changed significantly (avoid spam)
            if self.last_position is None or abs(progress_ms - self.last_position) > 2000:
                logger.info(f"[{timestamp}] {track_name} by {artist}")
                logger.info(f"         Progress: {progress_time}/{total_time} ({progress_pct:.1f}%) | State: {state} | Vol: {volume}")
                logger.info(f"         Raw values: progress_ms={progress_ms}, duration_ms={duration_ms}")
                self.last_position = progress_ms
        else:
            logger.info(f"[{timestamp}] {track_name} by {artist} | State: {state} | Vol: {volume}")
            logger.info(f"         No duration info: progress_ms={progress_ms}, duration_ms={duration_ms}")

async def main():
    """Main test function"""
    print("=== KitchenRadio Librespot Progress Test ===")
    print("This test uses the same KitchenRadioLibrespotClient that KitchenRadio uses.")
    print("It will show real-time progress updates when you play Spotify music.")
    print("Press Ctrl+C to exit.\n")
    
    test = LibrespotProgressTest()
    await test.test_progress_updates()

if __name__ == "__main__":
    # Run the test
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
