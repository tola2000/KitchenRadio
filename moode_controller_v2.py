#!/usr/bin/env python3
"""
MoOde Audio REST API Controller Library - Updated Version

This library provides a Python interface to control MoOde Audio servers
through their actual REST API endpoints used by the web interface.
"""

import requests
import json
import time
from typing import Optional, Dict, Any, List
import urllib.parse


class MoOdeAudioController:
    """
    A controller class for interacting with MoOde Audio server REST API.
    
    This version uses the actual API endpoints that MoOde's web interface uses.
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
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a HTTP request to the MoOde API.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            data: Request data for POST requests
            params: URL parameters
            
        Returns:
            Response data as dictionary or None if request failed
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                if data:
                    response = self.session.post(url, data=data, params=params, timeout=self.timeout)
                else:
                    response = self.session.post(url, params=params, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            
            # Try to parse JSON response, fallback to text
            try:
                return response.json()
            except json.JSONDecodeError:
                text_response = response.text.strip()
                if text_response:
                    return {"response": text_response}
                else:
                    return {"status": "ok"}
                
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with MoOde server: {e}")
            return None
    
    def get_status(self) -> Optional[Dict]:
        """
        Get current player status using MoOde's command interface.
        
        Returns:
            Dictionary containing player status information
        """
        # Use the correct MoOde command format
        result = self._make_request("/command/?cmd=status")
        if result is None:
            # Fallback to engine-mpd.php endpoint
            result = self._make_request("/engine-mpd.php", "POST", {"cmd": "status"})
        return result
    
    def _send_mpd_command(self, command: str) -> bool:
        """
        Send a command to MPD through MoOde's interface.
        
        Args:
            command: MPD command to send
            
        Returns:
            True if command was successful, False otherwise
        """
        # Try different MoOde API endpoints
        attempts = [
            # Primary endpoint - engine-mpd.php
            lambda: self._make_request("/engine-mpd.php", "POST", {"cmd": command}),
            # Alternative endpoint - engine-cmd.php  
            lambda: self._make_request("/engine-cmd.php", "POST", {"cmd": command}),
            # Command interface with GET
            lambda: self._make_request("/command/", "GET", params={"cmd": command}),
            # Command interface with POST
            lambda: self._make_request("/command/", "POST", {"cmd": command}),
        ]
        
        for attempt in attempts:
            try:
                result = attempt()
                if result is not None:
                    return True
            except Exception:
                continue
                
        return False
    
    def play(self) -> bool:
        """Start playback."""
        result = self._make_request("/command/?play")
        return result is not None
    
    def pause(self) -> bool:
        """Pause playback."""
        result = self._make_request("/command/?pause")
        return result is not None
    
    def stop(self) -> bool:
        """Stop playback."""
        result = self._make_request("/command/?stop")
        return result is not None
    
    def next_track(self) -> bool:
        """Skip to next track."""
        result = self._make_request("/command/?next")
        return result is not None
    
    def previous_track(self) -> bool:
        """Skip to previous track."""
        result = self._make_request("/command/?previous")
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
        
        # Use the correct MoOde Audio API syntax
        result = self._make_request(f"/command/?setvol%20{volume}")
        return result is not None
    
    def get_volume(self) -> Optional[int]:
        """
        Get current volume level.
        
        Returns:
            Current volume level (0-100) or None if failed
        """
        status = self.get_status()
        if status and 'volume' in status:
            try:
                return int(status['volume'])
            except (ValueError, TypeError):
                pass
        return None
    
    def get_current_song(self) -> Optional[Dict]:
        """
        Get information about the currently playing song.
        
        Returns:
            Dictionary with song information or None if failed
        """
        result = self._make_request("/command/?currentsong")
        if result is None:
            result = self._make_request("/engine-mpd.php", "POST", {"cmd": "currentsong"})
        return result
    
    def get_playlist(self) -> Optional[List[Dict]]:
        """
        Get current playlist.
        
        Returns:
            List of songs in playlist or None if failed
        """
        result = self._make_request("/command/?playlistinfo")
        if result is None:
            result = self._make_request("/engine-mpd.php", "POST", {"cmd": "playlistinfo"})
        return result
    
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
        result = self._make_request(f"/command/?seekcur%20{position}")
        return result is not None
    
    def get_system_info(self) -> Optional[Dict]:
        """
        Get system information from MoOde server.
        
        Returns:
            Dictionary with system information or None if failed
        """
        # Try to get system info through various endpoints
        endpoints = [
            "/engine-mpd.php",
            "/command/",
            "/sysinfo.php"
        ]
        
        for endpoint in endpoints:
            if endpoint == "/engine-mpd.php":
                result = self._make_request(endpoint, "POST", {"cmd": "stats"})
            elif endpoint == "/command/":
                result = self._make_request(endpoint, "GET", params={"cmd": "stats"})
            else:
                result = self._make_request(endpoint, "GET")
                
            if result:
                return result
                
        return None
    
    def is_connected(self) -> bool:
        """
        Check if the controller can connect to MoOde server.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to access the main page
            response = self.session.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                return True
                
            # Try alternative endpoint
            response = self.session.get(f"{self.base_url}/index.php", timeout=5)
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
        
        # Test basic functionality
        print("Testing basic commands...")
        
        status = controller.get_status()
        if status:
            print(f"Status: {status}")
        
        current_song = controller.get_current_song()
        if current_song:
            print(f"Current song: {current_song}")
        
        volume = controller.get_volume()
        if volume is not None:
            print(f"Current volume: {volume}%")
            
    else:
        print("Failed to connect to MoOde Audio server")
        print("Make sure MoOde is running and accessible")
