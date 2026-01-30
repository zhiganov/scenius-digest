import json
from http.server import BaseHTTPRequestHandler

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import config


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        groups = {}
        for key, cfg in config.MONITORED_GROUPS.items():
            groups[key] = {
                "name": cfg.get("name", key),
                "group_id": cfg.get("group_id"),
                "output_channel": cfg.get("output_channel"),
                "topics": list(cfg.get("topics", {}).keys()),
            }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"groups": groups}).encode())
