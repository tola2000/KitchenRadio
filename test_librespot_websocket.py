#!/usr/bin/env python3
"""
Simple test script to connect to go-librespot WebSocket and receive seek position updates.
This helps debug why progress bar might not be working.
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LibrespotWebSocketTest:
    def __init__(self, host="192.168.1.4", port=3678):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}/events"
        self.websocket = None
        
    async def connect_and_listen(self):
        """Connect to go-librespot WebSocket and listen for messages"""
        try:
            logger.info(f"Connecting to go-librespot WebSocket at {self.uri}")
            
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                logger.info("Connected successfully!")
                
                # Listen for messages
                async for message in websocket:
                    await self.handle_message(message)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
        except websockets.exceptions.InvalidURI:
            logger.error(f"Invalid WebSocket URI: {self.uri}")
        except ConnectionRefusedError:
            logger.error(f"Connection refused to {self.uri}. Is go-librespot running?")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
    
    async def handle_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            if message_type == 'seek':
                # This is what we're interested in for progress tracking
                position_ms = data.get('position_ms', 0)
                track_length_ms = data.get('track_length_ms', 0)
                
                if track_length_ms > 0:
                    progress_pct = (position_ms / track_length_ms) * 100
                    progress_time = f"{position_ms//60000:02d}:{(position_ms//1000)%60:02d}"
                    total_time = f"{track_length_ms//60000:02d}:{(track_length_ms//1000)%60:02d}"
                    
                    logger.info(f"[{timestamp}] SEEK: {progress_time}/{total_time} ({progress_pct:.1f}%)")
                    logger.info(f"         Raw: position_ms={position_ms}, track_length_ms={track_length_ms}")
                else:
                    logger.info(f"[{timestamp}] SEEK: position_ms={position_ms} (no track length)")
                    
            elif message_type == 'metadata':
                # Track information
                track_id = data.get('track_id', 'Unknown')
                name = data.get('name', 'Unknown')
                artist = data.get('artist', 'Unknown')
                album = data.get('album', 'Unknown')
                duration_ms = data.get('duration_ms', 0)
                
                duration_time = f"{duration_ms//60000:02d}:{(duration_ms//1000)%60:02d}"
                logger.info(f"[{timestamp}] METADATA: {name} by {artist}")
                logger.info(f"         Album: {album} | Duration: {duration_time}")
                logger.info(f"         Raw: duration_ms={duration_ms}")
                
            elif message_type == 'state':
                # Playback state changes
                state = data.get('state', 'unknown')
                logger.info(f"[{timestamp}] STATE: {state}")
                
            elif message_type == 'volume':
                # Volume changes
                volume = data.get('volume', 0)
                logger.info(f"[{timestamp}] VOLUME: {volume}")
                
            else:
                # Other message types
                logger.info(f"[{timestamp}] {message_type.upper()}: {data}")
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON message: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

async def main():
    """Main test function"""
    print("=== go-librespot WebSocket Test ===")
    print("This script will connect to go-librespot and show real-time updates.")
    print("Play some music on Spotify to see seek position updates.")
    print("Press Ctrl+C to exit.\n")
    
    # Test with default settings (localhost:24879)
    test = LibrespotWebSocketTest()
    
    try:
        await test.connect_and_listen()
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    # Check if required modules are available
    try:
        import websockets
    except ImportError:
        print("ERROR: websockets module not found!")
        print("Install it with: pip install websockets")
        exit(1)
    
    # Run the test
    asyncio.run(main())
