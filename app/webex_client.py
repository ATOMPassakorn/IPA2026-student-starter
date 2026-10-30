"""Part 4 student implementation."""

import os

import requests

WEBEX_API_BASE = 'https://webexapis.com/v1'

class WebexClient:
    def __init__(self, token=None, session=None):
        # TODO: implement according to Part 4 specification
        if token:
            self.token = token
        else:
            self.token = os.environ.get("WEBEX_BOT_TOKEN")
        if not self.token:
            raise PermissionError("Webex bot token is required")
        if session:
            self.session = session
        else:
            self.session = requests.Session()

    @property
    def headers(self):
        # TODO: implement according to Part 4 specification
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_message(self, message_id):
        # TODO: implement according to Part 4 specification
        response = self.session.get(f"{WEBEX_API_BASE}/messages/{message_id}", headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def download_file(self, file_url):
        # TODO: implement according to Part 4 specification
        response = self.session.get(file_url, timeout=10, headers=self.headers)
        response.raise_for_status()
        return response.content

    def send_message(self, room_id, text):
        # TODO: implement according to Part 4 specification
        response = self.session.post(f"{WEBEX_API_BASE}/messages", headers=self.headers,timeout=10, json={"roomId": room_id, "text": text})
        response.raise_for_status()
        return response.json()
