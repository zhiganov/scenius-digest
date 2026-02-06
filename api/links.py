import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import config
from lib.database import get_unpublished_links


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        days = int(query.get("days", ["7"])[0])
        group = query.get("group", [None])[0]
        include_all = query.get("all", [""])[0].lower() in ("true", "1")

        # Resolve group key to group_id
        group_id = None
        if group:
            if group in config.MONITORED_GROUPS:
                group_id = config.MONITORED_GROUPS[group].get("group_id")
            else:
                group_id = group

        links = get_unpublished_links(since_days=days, group_id=group_id, include_published=include_all)

        response = {
            "links": links,
            "count": len(links),
            "topics": {
                "links": len([l for l in links if l["topic"] == "links"]),
                "memes": len([l for l in links if l["topic"] == "memes"]),
            },
        }

        if group_id:
            response["group_id"] = group_id
        else:
            by_group = {}
            for link in links:
                gname = link.get("group_name") or "unknown"
                by_group[gname] = by_group.get(gname, 0) + 1
            response["by_group"] = by_group

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response, default=str).encode())
