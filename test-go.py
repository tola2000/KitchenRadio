import requests
import json

class GoLibrespotAPI:
    def __init__(self, base_url="http://localhost:3678"):
        self.base_url = base_url.rstrip("/")

    def _send_request(self, endpoint, method="GET", data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=json.dumps(data))
            elif method == "PUT":
                response = requests.put(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def get_status(self):
        return self._send_request("/status")

    def get_volume(self):
        return self._send_request("/volume")

    def set_volume(self, volume):
        if 0 <= volume <= 100:
            return self._send_request("/volume", method="POST", data={"volume": volume})
        else:
            print("Volume must be between 0 and 100.")
            return None

    def play(self):
        return self._send_request("/playback", method="POST", data={"play": True})

    def pause(self):
        return self._send_request("/playback", method="POST", data={"play": False})

    def next_track(self):
        return self._send_request("/playback/next", method="POST")

    def previous_track(self):
        return self._send_request("/playback/prev", method="POST")


if __name__ == "__main__":
    api = GoLibrespotAPI("http://192.168.1.4:3678")

    # Set volume to 50%
    api.set_volume(50)

    # Play music
    #api.play()

    # Get current status


    status = api.get_status()
    print("Current Status:", status)

    # Skip to next track
    api.next_track()