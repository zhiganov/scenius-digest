"""GET /api/events — unified events endpoint.

Merges Telegram event links (Supabase) with external event APIs (Luma).
Filters: ?community=nsrt, ?city=novi-sad, or no filter (all).
"""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import config
from lib.database import get_event_links
from lib.luma import fetch_luma_events


def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication: lowercase host, strip trailing slash."""
    try:
        parsed = urlparse(url)
        normalized = parsed._replace(
            netloc=parsed.netloc.lower(),
            path=parsed.path.rstrip('/'),
        )
        return normalized.geturl()
    except Exception:
        return url.rstrip('/').lower()


def _get_matching_groups(params: dict) -> dict:
    """Return groups matching the query params."""
    community = params.get("community", [None])[0]
    city = params.get("city", [None])[0]

    if community:
        cfg = config.MONITORED_GROUPS.get(community)
        if cfg:
            return {community: cfg}
        return {}
    elif city:
        return config.get_groups_by_city(city)
    else:
        return dict(config.MONITORED_GROUPS)


def _telegram_events_to_response(links: list[dict], group_key_by_id: dict) -> list[dict]:
    """Convert Supabase digest_links rows to response event dicts."""
    events = []
    for link in links:
        events.append({
            "id": f"tg-{link['id']}",
            "title": link.get("og_title") or link.get("title") or link.get("url"),
            "description": link.get("og_description") or link.get("description") or "",
            "image": link.get("og_image"),
            "url": link.get("url"),
            "starts_at": link.get("event_starts_at"),
            "ends_at": None,
            "location": link.get("event_location"),
            "source": "telegram",
            "community": group_key_by_id.get(link.get("group_id"), "unknown"),
        })
    return events


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        groups = _get_matching_groups(params)

        # Build reverse lookup: group_id -> group_key
        group_key_by_id = {
            str(cfg.get("group_id")): key for key, cfg in groups.items()
        }
        group_ids = list(group_key_by_id.keys())

        # Source A: Telegram event links from Supabase
        tg_links = get_event_links(group_ids=group_ids if group_ids else None)
        tg_events = _telegram_events_to_response(tg_links, group_key_by_id)

        # Source B: External event APIs (Luma, etc.)
        api_events = []
        for key, cfg in groups.items():
            for api_cfg in cfg.get("event_apis", []):
                if api_cfg.get("type") == "luma":
                    api_events.extend(fetch_luma_events(api_cfg["url"], key))

        # Deduplicate: if Telegram URL matches external API URL, prefer external version
        api_urls = {_normalize_url(e["url"]) for e in api_events}
        tg_events = [e for e in tg_events if _normalize_url(e["url"]) not in api_urls]

        # Merge and sort by starts_at ascending, nulls last
        all_events = api_events + tg_events
        all_events.sort(key=lambda e: (e.get("starts_at") is None, e.get("starts_at") or ""))

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"events": all_events}).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
