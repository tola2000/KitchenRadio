"""
KitchenRadio LibreSpot Client - Main client class for go-librespot interaction
"""

import logging
import requests
import json
from typing import Optional, Dict, Any

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
        
        # Construct base URL
        self.base_url = f"http://{host}:{port}"
        
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
                return True
            else:
                logger.error("Failed to get status from go-librespot")
                self._connected = False
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to go-librespot: {e}")
            self._connected = False
            return False
    
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
            if result and 'volume' in result:
                return int(result['volume'])
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
