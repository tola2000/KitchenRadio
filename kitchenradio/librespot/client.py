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
            return None
    
    def connect(self) -> bool:
        """
        Test connection to go-librespot server.
        
        Returns:
            True if connected successfully
        """
        try:
            logger.info(f"Testing connection to go-librespot at {self.base_url}")
            
            # Try to get status to test connection
            status = self.get_status()
            if status is not None:
                self._connected = True
                logger.info("Connected to go-librespot successfully")



                loop = asyncio.new_event_loop()
                t = threading.Thread(target=loop.run_forever, daemon=True)
                t.start()
                # store for later shutdown if needed
                self._ws_thread = t
                self._ws_loop = loop
                asyncio.run_coroutine_threadsafe(self.connect_ws(), loop)
                return True
            else:
                logger.error("Failed to get status from go-librespot")
                self._connected = False
                return False

            
                
        except Exception as e:
            logger.error(f"Failed to connect to go-librespot: {e}")
            self._connected = False
            return False
        
    async def connect_ws(self):
        try:
            logger.info(f"Connecting to go-librespot WebSocket at {self.wsurl}")

            async with websockets.connect(self.wsurl) as websocket:
                self.websocket = websocket
                logger.info("Connected successfully  {self.wsurl}!")
                
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
        for callback in self.callbacks['any']:
            try:
                callback(event='any', **kwargs)
            except Exception as e:
                logger.error(f"Error in 'any' callback for {event}: {e}")

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
            
            if message_type == 'metadata':
                self._trigger_callbacks('metadata', data=data)
                return
                
            elif message_type == 'state':
                self._trigger_callbacks('state', data=data)
                return
                
            elif message_type == 'volume':
                self._trigger_callbacks('volume', data=data)
                return

            else:
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
