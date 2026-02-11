"""Fetch future events from a guild.host community."""

import json
import logging
import re
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

_IMAGE_BASE = "https://ik.imagekit.io/guild/prod/tr:w-576,dpr-2"


def _resolve_image(relay_store: dict, cover_ref: dict | None) -> str | None:
    """Resolve a coverPhoto __ref to an ImageKit URL."""
    if not cover_ref or not isinstance(cover_ref, dict):
        return None
    ref_id = cover_ref.get("__ref")
    if not ref_id:
        return None
    image_obj = relay_store.get(ref_id)
    if not image_obj or image_obj.get("__typename") != "Image":
        return None
    row_id = image_obj.get("rowId")
    content_type = (image_obj.get("contentType") or "png").lower()
    ext = "jpg" if content_type == "jpeg" else content_type
    if row_id:
        return f"{_IMAGE_BASE}/{row_id}.{ext}"
    return None


def fetch_guildhost_events(guild_url: str, community_key: str) -> list[dict]:
    """Fetch future events from a guild.host community events page.

    Uses a Googlebot user-agent to get the SSR-rendered page which
    includes a Relay store in a <script> tag with event data.
    Returns list of normalized event dicts matching /api/events response shape.
    """
    if not guild_url:
        return []

    try:
        # guild.host serves SSR content to bot user-agents
        req = Request(guild_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Accept": "text/html",
        })
        with urlopen(req, timeout=15) as resp:
            html = resp.read(1048576).decode("utf-8", errors="replace")

        # Find the script tag containing the Relay store (has event data)
        relay_store = None
        for match in re.finditer(r"<script[^>]*>(.*?)</script>", html, re.DOTALL):
            script_content = match.group(1)
            if '"__typename":"Event"' not in script_content:
                continue
            try:
                relay_store = json.loads(script_content)
                break
            except (json.JSONDecodeError, ValueError):
                continue

        if not relay_store:
            logger.warning(f"No Relay store with events found on {guild_url}")
            return []

        now = datetime.now(timezone.utc)
        events = []

        for key, value in relay_store.items():
            if not isinstance(value, dict):
                continue
            if value.get("__typename") != "Event":
                continue
            if value.get("visibility") != "LISTED":
                continue

            start_at = value.get("startAt")
            end_at = value.get("endAt")

            # Filter to future events only
            if start_at:
                try:
                    event_start = datetime.fromisoformat(start_at)
                    if event_start < now:
                        continue
                except (ValueError, TypeError):
                    pass

            pretty_url = value.get("prettyUrl", "")
            event_url = f"https://guild.host/events/{pretty_url}" if pretty_url else guild_url
            image_url = _resolve_image(relay_store, value.get("coverPhoto"))

            events.append({
                "id": f"guildhost-{value.get('rowId', key)}",
                "title": value.get("name", "Untitled"),
                "description": "",
                "image": image_url,
                "url": event_url,
                "starts_at": start_at,
                "ends_at": end_at,
                "location": None,
                "source": "guildhost",
                "community": community_key,
            })

        # Sort by start time
        events.sort(key=lambda e: (e["starts_at"] is None, e["starts_at"] or ""))
        return events

    except (URLError, OSError, ValueError, KeyError) as e:
        logger.error(f"Failed to fetch guild.host events from {guild_url}: {e}")
        return []
