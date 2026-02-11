"""Extract structured event data from known platforms (Luma, Meetup, Eventbrite)."""

import json
import re
import logging
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

PLATFORM_PATTERNS = [
    (re.compile(r'https?://(?:www\.)?(?:lu\.ma|luma\.com)/([^/?#]+)'), 'luma'),
    (re.compile(r'https?://(?:www\.)?meetup\.com/.+/events/'), 'meetup'),
    (re.compile(r'https?://(?:www\.)?eventbrite\.com/e/'), 'eventbrite'),
]

LD_JSON_PATTERN = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def detect_platform(url: str) -> str | None:
    """Returns 'luma', 'meetup', 'eventbrite', or None."""
    for pattern, name in PLATFORM_PATTERNS:
        if pattern.search(url):
            return name
    return None


def enrich_event(url: str, html: str = None) -> dict:
    """Extract event metadata from a URL. Returns {starts_at, ends_at, location} or {}.

    For Luma: calls public API (no HTML needed).
    For Meetup/Eventbrite: parses ld+json from HTML. Fetches HTML if not provided.
    """
    platform = detect_platform(url)
    if not platform:
        return {}

    try:
        if platform == 'luma':
            return _enrich_luma(url)
        else:
            return _enrich_ldjson(url, html)
    except Exception as e:
        logger.debug(f"Event enrichment failed for {url}: {e}")
        return {}


def _enrich_luma(url: str) -> dict:
    """Fetch event data from Luma public API."""
    slug = url.rstrip('/').split('/')[-1].split('?')[0]
    api_url = f"https://api.lu.ma/event/get?event_api_id={slug}"

    req = Request(api_url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; SceniusDigestBot/1.0)",
        "Accept": "application/json",
    })
    with urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read(65536))

    event = data.get("event", {})
    result = {}
    if event.get("start_at"):
        result["starts_at"] = event["start_at"]
    if event.get("end_at"):
        result["ends_at"] = event["end_at"]
    geo = event.get("geo_address_info") or {}
    if geo.get("full_address"):
        result["location"] = geo["full_address"]
    return result


def _enrich_ldjson(url: str, html: str = None) -> dict:
    """Parse ld+json Event schema from HTML."""
    if not html:
        html = _fetch_html(url, max_bytes=262144)
    if not html:
        return {}

    for match in LD_JSON_PATTERN.finditer(html):
        try:
            ld = json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            continue

        # Handle both single objects and arrays
        items = ld if isinstance(ld, list) else [ld]
        for item in items:
            if item.get("@type") == "Event":
                return _parse_ld_event(item)

    return {}


def _parse_ld_event(item: dict) -> dict:
    result = {}
    if item.get("startDate"):
        result["starts_at"] = item["startDate"]
    if item.get("endDate"):
        result["ends_at"] = item["endDate"]

    location = item.get("location", {})
    if isinstance(location, dict):
        parts = []
        if location.get("name"):
            parts.append(location["name"])
        addr = location.get("address", {})
        if isinstance(addr, dict) and addr.get("streetAddress"):
            parts.append(addr["streetAddress"])
        elif isinstance(addr, str):
            parts.append(addr)
        if parts:
            result["location"] = ", ".join(parts)

    return result


def _fetch_html(url: str, max_bytes: int = 262144) -> str | None:
    """Fetch HTML from URL. Returns decoded string or None."""
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; SceniusDigestBot/1.0)",
            "Accept": "text/html",
        })
        with urlopen(req, timeout=5) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return None
            raw = resp.read(max_bytes)
        return raw.decode("utf-8", errors="replace")
    except (URLError, OSError, ValueError) as e:
        logger.debug(f"HTML fetch failed for {url}: {e}")
        return None
