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
    (re.compile(r'https?://(?:www\.)?eventbrite\.[a-z.]+/e/'), 'eventbrite'),
]

# A URL is treated as an event page (for date-enrichment and for filtering the
# events endpoint) when it's a known platform or has an event-ish path. This keeps
# real events, even undated ones like Zoom registration pages, and excludes bare
# resource links (YouTube, plain homepages, surveys).
EVENT_URL_RE = re.compile(
    r'(?:'
    r'lu\.ma/|luma\.com/|meetup\.com/.+/events/|eventbrite\.[a-z.]+/e/|'
    r'addevent\.com/event/|guild\.host/|hopin\.com/|airmeet\.com/|'
    r'/(?:events?|webinars?|seminars?|tickets|register)(?:/|$|\?)'
    r')',
    re.IGNORECASE,
)

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
    try:
        if platform == 'luma':
            return _enrich_luma(url)
        # ld+json for known HTML platforms and any event-ish URL (generic fallback)
        if platform in ('meetup', 'eventbrite') or EVENT_URL_RE.search(url):
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
    """Parse ld+json Event schema from HTML (handles arrays, @graph, Event subtypes)."""
    if not html:
        html = _fetch_html(url, max_bytes=262144)
    if not html:
        return {}

    for match in LD_JSON_PATTERN.finditer(html):
        try:
            ld = json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            continue
        for item in _iter_ld_items(ld):
            if _is_event_type(item.get("@type")):
                parsed = _parse_ld_event(item)
                if parsed.get("starts_at"):
                    return parsed

    return {}


def _iter_ld_items(ld):
    """Yield every dict in an ld+json blob, descending into lists and @graph."""
    stack = [ld]
    while stack:
        cur = stack.pop()
        if isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, dict):
            yield cur
            graph = cur.get("@graph")
            if isinstance(graph, list):
                stack.extend(graph)


def _is_event_type(type_value) -> bool:
    """True for schema.org Event or any subtype (EducationEvent, BusinessEvent, ...)."""
    if isinstance(type_value, list):
        return any(_is_event_type(t) for t in type_value)
    return isinstance(type_value, str) and (type_value == "Event" or type_value.endswith("Event"))


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
