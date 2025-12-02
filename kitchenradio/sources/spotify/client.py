"""
KitchenRadio LibreSpot Client - Main client class for go-librespot interaction
"""

import logging
import requests
import json
from typing import Optional, Dict, Any, Callable
import websockets
import asyncio, threading
import asyncio

logger = logging.getLogger(__name__)


class KitchenRadioLibrespotClient:
    """
    go-librespot client with KitchenRadio-specific functionality.
    """
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 3678,
                 timeout: int = 10):
        """
        Initialize KitchenRadio go-librespot client.
        
        Args:
            host: go-librespot server hostname
            port: go-librespot server port (default 3678)
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._connected = False
        self.websocket = None
        self.callbacks = {}

        # Construct base URL
        self.base_url = f"http://{host}:{port}"
        self.wsurl = f"ws://{host}:{port}/events"
        
        logger.info(f"KitchenRadio LibreSpot client initialized for {self.base_url}")
    
    def _send_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Send HTTP request to go-librespot API.
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST, PUT)
            data: Request data for POST/PUT
            
        Returns:
            Response data or None if error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=self.timeout)
            elif method == "PUT":
                response = requests.put(url, headers=headers, data=json.dumps(data), timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Check if response has content
            if not response.text or response.text.strip() == '':
                # Empty response can be valid (e.g., 204 No Content or when no device connected)
                # Only log as debug, not error
                logger.debug(f"Empty response from {url} (status: {response.status_code})")
                return {} if response.status_code == 200 else None
            
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {url}")
            self._connected = False
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {url}: {e}")
            # Log the actual response content for debugging
            if 'response' in locals():
                logger.error(f"Response status: {response.status_code}, content length: {len(response.text)}")
                logger.error(f"Response content: {response.text[:500]}")
            return None
    
    def connect(self, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        """
        Test connection to go-librespot server with retry logic.
        
        Tests if the server is responding by attempting a simple HTTP request.
        Empty responses are acceptable - they just mean no device is connected yet.
        
        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay in seconds between retries
        
        Returns:
            True if server is responding (even with empty data)
        """
        import time
        
        try:
            logger.info(f"Testing connection to go-librespot at {self.base_url}")
            
            # Try to reach the server with retries
            for attempt in range(max_retries):
                try:
                    # Simple GET request to test if server is responding
                    # We don't care about the response data - just that we can reach it
                    response = requests.get(
                        f"{self.base_url}/status",
                        timeout=self.timeout
                    )
                    
                    # Server responded! Even 204 No Content or empty response is fine
                    if response.status_code in [200, 204]:
                        self._connected = True
                        logger.info(f"✅ go-librespot server is responding (status: {response.status_code})")
                        
                        # Start WebSocket connection
                        loop = asyncio.new_event_loop()
                        t = threading.Thread(target=loop.run_forever, daemon=True)
                        t.start()
                        # store for later shutdown if needed
                        self._ws_thread = t
                        self._ws_loop = loop
                        asyncio.run_coroutine_threadsafe(self.connect_ws(), loop)
                        return True
                    else:
                        logger.warning(f"Unexpected status code: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    # Connection error - server not reachable
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Cannot reach go-librespot server after {max_retries} attempts: {e}")
                        self._connected = False
                        return False
            
            return False
                
        except Exception as e:
            logger.error(f"Failed to connect to go-librespot: {e}")
            self._connected = False
            return False
        
    async def connect_ws(self):
        """Connect to WebSocket and automatically reconnect if connection drops"""
        reconnect_delay = 2.0
        max_reconnect_delay = 30.0
        
        while True:  # Auto-reconnect loop
            try:
                logger.info(f"Connecting to go-librespot WebSocket at {self.wsurl}")

                async with websockets.connect(self.wsurl) as websocket:
                    self.websocket = websocket
                    logger.info("Connected successfully  {self.wsurl}!")
                    reconnect_delay = 2.0  # Reset delay on successful connection
                    
                    # Listen for messages
                    async for message in websocket:
                        await self.handle_message(message)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed - reconnecting...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)  # Exponential backoff
            except websockets.exceptions.InvalidURI:
                logger.error(f"Invalid WebSocket URI: {self.wsurl}")
                break  # Don't retry on invalid URI
            except ConnectionRefusedError:
                logger.warning(f"Connection refused to {self.wsurl}. Server may be restarting, retrying in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
            except Exception as e:
                logger.warning(f"WebSocket error: {e}, reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)

    def add_callback(self, event: str, callback: Callable):
        """
        Add callback for specific event.
        
        Args:
            event: Event name (track_started, track_paused, track_resumed, track_ended, volume_changed, state_changed)
            callback: Callback function
        """
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        logger.debug(f"Added callback for {event}")

    def _trigger_callbacks(self, event: str, **kwargs):
        """Trigger callbacks for event."""
        # Trigger 'any' callbacks if registered
        if 'any' in self.callbacks:
            for callback in self.callbacks['any']:
                try:
                    callback(event=event, **kwargs)
                except Exception as e:
                    logger.error(f"Error in 'any' callback for {event}: {e}")

        # Trigger specific event callbacks
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    logger.error(f"Error in callback for {event}: {e}")

    async def handle_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            logger.debug(f"[Spotify WebSocket] Received message type: {message_type}")
            
            if message_type == 'metadata':
                logger.debug(f"[Spotify WebSocket] Metadata event: {data}")
                self._trigger_callbacks('metadata', data=data)
                return
                
            elif message_type == 'state':
                logger.debug(f"[Spotify WebSocket] State event: {data}")
                self._trigger_callbacks('state', data=data)
                return
                
            elif message_type == 'volume':
                logger.debug(f"[Spotify WebSocket] Volume event: {data}")
                self._trigger_callbacks('volume', data=data)
                return

            else:
                logger.debug(f"[Spotify WebSocket] Other event: {message_type}")
                self._trigger_callbacks('other', data=data)
                return

        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON message: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    
    def disconnect(self):
        """Disconnect from go-librespot server."""
        logger.info("Disconnecting from go-librespot")
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to go-librespot server."""
        return self._connected
    
    # Playback control methods
    def play(self) -> bool:
        """Start playback."""
        try:
            result = self._send_request("/playback", method="POST", data={"play": True})
            if result is not None:
                logger.info("Started playback")
                return True
            return False
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            return False
    
    def pause(self) -> bool:
        """Pause playback."""
        try:
            result = self._send_request("/player/pause", method="POST", data={"play": False})

            logger.info("Paused playback")
            return True

        except Exception as e:
            logger.error(f"Error pausing playback: {e}")
            return False

    def stop(self) -> bool:
        """Pause playback."""
        try:
            result = self._send_request("/player/pause", method="POST", data={"play": False})

            logger.info("Paused playback")
            return True

        except Exception as e:
            logger.error(f"Error pausing playback: {e}")
            return False
        
    def playpause(self) -> bool:
        """playpause playback."""
        try:
            result = self._send_request("/player/playpause", method="POST", data={"play": False})

            logger.info("playpause playback")
            return True

        except Exception as e:
            logger.error(f"Error playpause playback: {e}")
            return False


    def resume(self) -> bool:
        """Pause playback."""
        try:
            result = self._send_request("/player/resume", method="POST", data={"play": False})

            logger.info("resume playback")
            return True

        except Exception as e:
            logger.error(f"Error resume playback: {e}")
            return False

    def next_track(self) -> bool:
        """Skip to next track."""
        try:
            result = self._send_request("/player/next", method="POST")
            # if result is not None:
            #     logger.info("Skipped to next track")
            #     return True
            # return False
            logger.info("Skipped to next track")
            return True
        except Exception as e:
            logger.error(f"Error skipping to next: {e}")
            return False
        

    def previous_track(self) -> bool:
        """Skip to previous track."""
        try:
            result = self._send_request("/player/prev", method="POST")
            # if result is not None:
            #     logger.info("Skipped to previous track")
            #     return True
            # return False
            logger.info("Skipped to previous track")
            return True
        except Exception as e:
            logger.error(f"Error skipping to previous: {e}")
            return False
    
    # Volume control
    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)."""
        try:
            if not 0 <= volume <= 100:
                raise ValueError("Volume must be between 0 and 100")
            
            result = self._send_request("/player/volume", method="POST", data={"volume": volume})
          #  if result is not None:
            logger.info(f"Set volume to {volume}%")
            return True
           # return False
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    def get_volume(self) -> Optional[int]:
        """Get current volume."""
        try:
            result = self._send_request("/player/volume")
            if result and 'value' in result:
                return int(result['value'])
            return None
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return None
    
    # Status and info
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get player status."""
        try:
            return self._send_request("/status")
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None
    
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """Get current track info from status."""
        try:
            status = self.get_status()
            if status and 'track' in status:
                return status['track']
            return None
        except Exception as e:
            logger.error(f"Error getting current track: {e}")
            return None
    
    # Additional LibreSpot-specific methods
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get current track metadata."""
        try:
            return self._send_request("/metadata")
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            return None
    
    def get_devices(self) -> Optional[Dict[str, Any]]:
        """Get available devices."""
        try:
            return self._send_request("/devices")
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return None
    
    # Shuffle and repeat control
    def set_shuffle(self, enabled: bool) -> bool:
        """Set shuffle mode."""
        try:
            result = self._send_request("/player/shuffle", method="POST", data={"shuffle": enabled})
            logger.info(f"Set shuffle to {enabled}")
            return True
        except Exception as e:
            logger.error(f"Error setting shuffle: {e}")
            return False
    
    def get_shuffle(self) -> Optional[bool]:
        """Get current shuffle state."""
        try:
            result = self._send_request("/player/shuffle")
            if result and 'value' in result:
                return bool(result['value'])
            return None
        except Exception as e:
            logger.error(f"Error getting shuffle state: {e}")
            return None
    
    def set_repeat(self, mode: str) -> bool:
        """Set repeat mode (off, track, context)."""
        try:
            result = self._send_request("/player/repeat", method="POST", data={"repeat": mode})
            logger.info(f"Set repeat to {mode}")
            return True
        except Exception as e:
            logger.error(f"Error setting repeat: {e}")
            return False
    
    def get_repeat(self) -> Optional[str]:
        """Get current repeat mode."""
        try:
            result = self._send_request("/player/repeat")
            if result and 'value' in result:
                return str(result['value'])
            return None
        except Exception as e:
            logger.error(f"Error getting repeat mode: {e}")
            return None
