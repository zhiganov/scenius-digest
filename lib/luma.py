"""Fetch future events from a Luma calendar."""

import json
import logging
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)


def fetch_luma_events(calendar_url: str, community_key: str, api_id: str | None = None) -> list[dict]:
    """Fetch future events from a Luma calendar.

    Uses api_id if provided, otherwise extracts slug from URL.
    Calls api.lu.ma/calendar/get-items.
    Returns list of normalized event dicts matching /api/events response shape.
    """
    if not calendar_url and not api_id:
        return []

    try:
        calendar_api_id = api_id or calendar_url.rstrip('/').split('/')[-1]
        api_url = f"https://api.lu.ma/calendar/get-items?calendar_api_id={calendar_api_id}&period=future"

        req = Request(api_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; SceniusDigestBot/1.0)",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read(262144))

        events = []
        for entry in data.get("entries", []):
            event = entry.get("event", {})
            event_url = f"https://luma.com/{event.get('url', calendar_api_id)}"

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
