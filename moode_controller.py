#!/usr/bin/env python3
"""
MoOde Audio REST API Controller Library

This library provides a Python interface to control MoOde Audio servers
through their REST API endpoints.
"""

import requests
import json
import time
from typing import Optional, Dict, Any, List
import urllib.parse


class MoOdeAudioController:
    """
    A controller class for interacting with MoOde Audio server REST API.
    
    MoOde Audio is a popular audiophile-quality music player for Raspberry Pi.
    This class provides methods to control playback, manage playlists, and
    retrieve system information.
    """
    
    def __init__(self, host: str = "localhost", port: int = 80, timeout: int = 10):
        """
        Initialize the MoOde Audio controller.
        
        Args:
            host: MoOde server hostname or IP address
            port: MoOde server port (default: 80)
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a HTTP request to the MoOde API.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            data: Request data for POST requests
            
        Returns:
            Response data as dictionary or None if request failed
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            
            # Try to parse JSON response, fallback to text
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"response": response.text}
                
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with MoOde server: {e}")
            return None
    
    def get_status(self) -> Optional[Dict]:
        """
        Get current player status.
        
        Returns:
            Dictionary containing player status information
        """
        return self._make_request("/command/?cmd=status")
    
    def play(self) -> bool:
        """
        Start playback.
        
        Returns:
            True if command was successful, False otherwise
        """
        result = self._make_request("/command/?cmd=play")
        return result is not None
    
    def pause(self) -> bool:
        """
        Pause playback.
        
        Returns:
            True if command was successful, False otherwise
        """
        result = self._make_request("/command/?cmd=pause")
        return result is not None
    
    def stop(self) -> bool:
        """
        Stop playback.
        
        Returns:
            True if command was successful, False otherwise
        """
        result = self._make_request("/command/?cmd=stop")
        return result is not None
    
    def next_track(self) -> bool:
        """
        Skip to next track.
        
        Returns:
            True if command was successful, False otherwise
        """
        result = self._make_request("/command/?cmd=next")
        return result is not None
    
    def previous_track(self) -> bool:
        """
        Skip to previous track.
        
        Returns:
            True if command was successful, False otherwise
        """
        result = self._make_request("/command/?cmd=previous")
        return result is not None
    
    def set_volume(self, volume: int) -> bool:
        """
        Set playback volume.
        
        Args:
            volume: Volume level (0-100)
            
        Returns:
            True if command was successful, False otherwise
        """
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be between 0 and 100")
            
        result = self._make_request(f"/command/?cmd=setvol%20{volume}")
        return result is not None
    
    def get_volume(self) -> Optional[int]:
        """
        Get current volume level.
        
        Returns:
            Current volume level (0-100) or None if failed
        """
        status = self.get_status()
        if status and 'volume' in status:
            return int(status['volume'])
        return None
    
    def get_current_song(self) -> Optional[Dict]:
        """
        Get information about the currently playing song.
        
        Returns:
            Dictionary with song information or None if failed
        """
        return self._make_request("/command/?cmd=currentsong")
    
    def get_playlist(self) -> Optional[List[Dict]]:
        """
        Get current playlist.
        
        Returns:
            List of songs in playlist or None if failed
        """
        return self._make_request("/command/?cmd=playlistinfo")
    
    def toggle_playback(self) -> bool:
        """
        Toggle between play and pause.
        
        Returns:
            True if command was successful, False otherwise
        """
        status = self.get_status()
        if status:
            state = status.get('state', '').lower()
            if state == 'play':
                return self.pause()
            else:
                return self.play()
        return False
    
    def seek(self, position: float) -> bool:
        """
        Seek to a specific position in the current track.
        
        Args:
            position: Position in seconds
            
        Returns:
            True if command was successful, False otherwise
        """
        result = self._make_request(f"/command/?cmd=seek&pos={position}")
        return result is not None
    
    def get_system_info(self) -> Optional[Dict]:
        """
        Get system information from MoOde server.
        
        Returns:
            Dictionary with system information or None if failed
        """
        return self._make_request("/command/?cmd=get_system_info")
    
    def is_connected(self) -> bool:
        """
        Check if the controller can connect to MoOde server.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def wait_for_connection(self, max_attempts: int = 10, delay: float = 1.0) -> bool:
        """
        Wait for MoOde server to become available.
        
        Args:
            max_attempts: Maximum number of connection attempts
            delay: Delay between attempts in seconds
            
        Returns:
            True if connection established, False if timeout
        """
        for attempt in range(max_attempts):
            if self.is_connected():
                return True
            if attempt < max_attempts - 1:
                time.sleep(delay)
        return False


def create_controller(host: str = "localhost", port: int = 80) -> MoOdeAudioController:
    """
    Factory function to create a MoOde Audio controller instance.
    
    Args:
        host: MoOde server hostname or IP address
        port: MoOde server port
        
    Returns:
        MoOdeAudioController instance
    """
    return MoOdeAudioController(host, port)


if __name__ == "__main__":
    # Example usage
    controller = create_controller()
    
    if controller.is_connected():
        print("Connected to MoOde Audio server")
        status = controller.get_status()
        if status:
            print(f"Current status: {status}")
    else:
        print("Failed to connect to MoOde Audio server")
