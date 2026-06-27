import json
import os
from http.server import BaseHTTPRequestHandler

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import auth, config

# group_id + output_channel are Telegram internals (source-group / output-channel
# chat IDs). They are exposed only to callers presenting the read-only config
# secret (e.g. the Avails bot, which posts with its own bot token). Public
# callers get name/topics/city/event metadata only. See issue #13.
CONFIG_READ_SECRET = os.environ.get("CONFIG_READ_SECRET")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        member_ids = auth.member_ids_from_request(self.headers)
        authorized = bool(CONFIG_READ_SECRET) and (
            self.headers.get("Authorization", "") == f"Bearer {CONFIG_READ_SECRET}"
        )

        groups = {}
        for key, cfg in config.visible_groups(config.MONITORED_GROUPS, member_ids).items():
            entry = {
                "name": cfg.get("name", key),
                "topics": cfg.get("topics", {}),
                "city": cfg.get("city"),
                "event_topics": cfg.get("event_topics", []),
                "event_apis": cfg.get("event_apis", []),
            }
            if authorized:
                entry["group_id"] = cfg.get("group_id")
                entry["output_channel"] = cfg.get("output_channel")
            groups[key] = entry

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"groups": groups}).encode())
