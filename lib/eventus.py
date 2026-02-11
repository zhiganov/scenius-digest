"""Fetch future events from an eventus.city community."""

import json
import logging
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)


def fetch_eventus_events(city_url: str, community_key: str, city_id: str | None = None) -> list[dict]:
    """Fetch future events from eventus.city for a city.

    Uses the /api/get-city-userevents endpoint.
    city_id can be provided explicitly or extracted from the URL path
    (e.g. https://eventus.city/in/novi_sad uses city_id from config).
    Returns list of normalized event dicts matching /api/events response shape.
    """
    if not city_url and not city_id:
        return []

    try:
        api_url = f"https://eventus.city/api/get-city-userevents?city_id={city_id}"

        req = Request(api_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; SceniusDigestBot/1.0)",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read(262144))

        now = datetime.now(timezone.utc)
        events = []

        for date_group in data.get("events", []):
            for event in date_group.get("events", []):
                start_date = event.get("start_date", "")
                start_time = event.get("start_time", "00:00")

                # Parse DD.MM.YYYY + HH:MM into ISO format
                starts_at = None
                if start_date:
                    try:
                        dt = datetime.strptime(
                            f"{start_date} {start_time}", "%d.%m.%Y %H:%M"
                        ).replace(tzinfo=timezone.utc)
                        if dt < now:
                            continue
                        starts_at = dt.isoformat()
                    except (ValueError, TypeError):
                        pass

                # Compute end time from spend_time (hours)
                ends_at = None
                spend_time = event.get("spend_time")
                if starts_at and spend_time:
                    try:
                        hours = float(spend_time)
                        from datetime import timedelta
                        end_dt = dt + timedelta(hours=hours)
                        ends_at = end_dt.isoformat()
                    except (ValueError, TypeError):
                        pass

                link = event.get("link")
                event_id = event.get("id", "")
                photo = event.get("full_photo_url") or event.get("photo_url")
                image_url = f"https://eventus.city/{photo}" if photo else None

                events.append({
                    "id": f"eventus-{event_id}",
                    "title": event.get("title", "Untitled"),
                    "description": "",
                    "image": image_url,
                    "url": link or city_url,
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                    "location": None,
                    "source": "eventus",
                    "community": community_key,
                })

        events.sort(key=lambda e: (e["starts_at"] is None, e["starts_at"] or ""))
        return events

    except (URLError, OSError, ValueError, KeyError) as e:
        logger.error(f"Failed to fetch eventus.city events from {api_url}: {e}")
        return []
