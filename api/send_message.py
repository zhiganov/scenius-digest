import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.telegram import send_message


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            secret = os.getenv("WEBHOOK_SECRET")
            if secret:
                auth = self.headers.get("Authorization", "")
                if auth != f"Bearer {secret}":
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(b'{"error":"unauthorized"}')
                    return

            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length))

            chat_id = body.get("chat_id")
            text = body.get("text")
            if not chat_id or not text:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error":"chat_id and text required"}')
                return

            result = send_message(chat_id, text)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
