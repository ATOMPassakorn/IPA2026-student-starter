"""Part 4 student implementation."""

import json

import logging

import os

from concurrent.futures import ThreadPoolExecutor

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pathlib import Path

from tempfile import TemporaryDirectory

from app.integration import process_request

from app.webex_client import WEBEX_API_BASE, WebexClient

class WebexEventHandler:
    def __init__(self, client, bot_person_id, processor=None):
        # TODO: implement according to Part 4 specification
        self.client = client
        self.bot_person_id = bot_person_id
        if processor:
            self.processor = processor
        else:
            self.processor = process_request

    def handle_event(self, event):
        # TODO: implement according to Part 4 specification
        if event.get("resource") != "messages" and event.get("event") != "created":
                return None
        if event.get("data") is None and event.get("id") is None:
            return None
        if event.get("data", {}).get("personId") == self.bot_person_id:
            return None
        message_id = event.get("data", {}).get("id")
        if not message_id:
            return None
        message = self.client.get_message(message_id)
        if message.get("personId") == self.bot_person_id:
            return None
        room_id = message["roomId"]
        files = message.get("files", [])
        if len(files) == 0:
            res = self.processor(message.get("mentionedPeople", []), None, self.bot_person_id)
        elif len(files) > 1:
            res = {"status": "error", "result": "multiple_attachments"}
        else:
            content = self.client.download_file(files[0])
            with TemporaryDirectory() as tmpdir:
                temp_path = Path(tmpdir) / "request.yaml"
                temp_path.write_bytes(content)
                res = self.processor(message.get("mentionedPeople", []), temp_path, self.bot_person_id)
        self.client.send_message(room_id, json.dumps(res))
        return res

def make_http_handler(submit_event):
    # TODO: implement according to Part 4 specification
    class WebhookHTTPHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "result": "healthy"}).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
        def do_POST(self):
            if self.path == "/webhook":
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                except (ValueError, TypeError):
                    content_length = 0
                if content_length < 1 or content_length > 1_000_000:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "result": "invalid_event"}).encode("utf-8"))
                    return
                body = self.rfile.read(content_length)
                try:
                    event = json.loads(body.decode("utf-8"))
                    if not isinstance(event, dict):
                        raise ValueError()
                except Exception:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "result": "invalid_event"}).encode("utf-8"))
                    return
                submit_event(event)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "result": "accepted"}).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, format, *args):
            pass
    return WebhookHTTPHandler

def main():
    # TODO: implement according to Part 4 specification
    host = os.environ.get("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.environ.get("WEBHOOK_PORT", "8000"))

    token = os.environ.get("WEBEX_BOT_TOKEN")
    if token:
        client = WebexClient(token=token)
    else:
        client = None

    executor = ThreadPoolExecutor(max_workers=1)

    def process_event(event):
        if client:
            me = client.session.get(f"{WEBEX_API_BASE}/people/me", headers=client.headers).json()
            bot_person_id = me["id"]
            handler = WebexEventHandler(client, bot_person_id=bot_person_id)
            handler.handle_event(event)
    server = ThreadingHTTPServer((host, port), make_http_handler(lambda e: executor.submit(process_event, e)))
    print(f"Webhook server running on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == "__main__":
    main()
