"""Fetch future events from a Luma calendar."""

import json
import logging
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)


def fetch_luma_events(calendar_url: str, community_key: str) -> list[dict]:
    """Fetch future events from a Luma calendar.

    Extracts slug from URL, calls api.lu.ma/calendar/get-items.
    Returns list of normalized event dicts matching /api/events response shape.
    """
    if not calendar_url:
        return []

    try:
        slug = calendar_url.rstrip('/').split('/')[-1]
        api_url = f"https://api.lu.ma/calendar/get-items?calendar_api_id={slug}&period=future"

        req = Request(api_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; SceniusDigestBot/1.0)",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read(262144))

        events = []
        for entry in data.get("entries", []):
            event = entry.get("event", {})
            event_url = f"https://lu.ma/{event.get('url', slug)}"

            geo = event.get("geo_address_info") or {}

            events.append({
                "id": f"luma-{event.get('api_id', '')}",
                "title": event.get("name", "Untitled"),
                "description": event.get("description_short", ""),
                "image": event.get("cover_url"),
                "url": event_url,
                "starts_at": event.get("start_at"),
                "ends_at": event.get("end_at"),
                "location": geo.get("full_address"),
                "source": "luma",
                "community": community_key,
            })

        return events

    except (URLError, OSError, ValueError, KeyError) as e:
        logger.error(f"Failed to fetch Luma events from {calendar_url}: {e}")
        return []
