"""One-shot endpoint to backfill OG metadata for existing links missing it."""

import json
import os
import logging
from http.server import BaseHTTPRequestHandler

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.database import get_client
from lib.opengraph import fetch_og

logger = logging.getLogger(__name__)

# Simple bearer token to prevent abuse
BACKFILL_SECRET = os.getenv("WEBHOOK_SECRET", "")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Require the same secret as the webhook
        auth = self.headers.get("Authorization", "")
        if BACKFILL_SECRET and auth != f"Bearer {BACKFILL_SECRET}":
            self.send_response(403)
            self.end_headers()
            return

        client = get_client()

        # Fetch links where og_title is null
        result = (
            client.table("digest_links")
            .select("id, url")
            .is_("og_title", "null")
            .order("id")
            .execute()
        )

        links = result.data or []
        updated = 0
        errors = 0

        for link in links:
            og = fetch_og(link["url"])
            # Only update if we got at least a title
            if og.get("og_title"):
                update = {}
                if og["og_title"]:
                    update["og_title"] = og["og_title"]
                if og["og_description"]:
                    update["og_description"] = og["og_description"]
                if og["og_image"]:
                    update["og_image"] = og["og_image"]

                try:
                    client.table("digest_links").update(update).eq("id", link["id"]).execute()
                    updated += 1
                    logger.info(f"Backfilled OG for {link['url']}: {og['og_title']}")
                except Exception as e:
                    errors += 1
                    logger.error(f"Failed to update {link['id']}: {e}")
            else:
                logger.debug(f"No OG data for {link['url']}")

        body = json.dumps({
            "total": len(links),
            "updated": updated,
            "errors": errors,
        })

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())
