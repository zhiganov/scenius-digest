"""Tests for GET /api/events — Source C (manual events, community-admin#6 / V6).

Sources A (Telegram/Supabase) and B (Luma/guild.host) are stubbed so these
tests exercise the merge + visibility-gate logic in isolation, no real
network/DB I/O, mirroring how tests/test_config.py isolates lib.config's
own network calls.

Coverage required by the task brief:
- a manual event whose community IS in the visible `groups` is merged
- one whose community is NOT in `groups` (private, or unknown) is dropped
- a fetch failure inside _fetch_manual_events degrades gracefully —
  Telegram + Luma events are still returned, and no exception propagates
"""

import io
import json
import urllib.error
import urllib.request

import pytest

from api import events as events_module
from lib import config


# Two communities: "visible" is public, "private" is private with no caller
# membership (the handler is invoked with no Authorization header below), so
# config.visible_groups drops it before Source C ever sees it.
GROUPS = {
    "visible": {
        "group_id": "111",
        "visibility": "public",
        "event_apis": [
            {"type": "luma", "url": "https://lu.ma/visible-cal", "api_id": "visible-cal"},
        ],
    },
    "private": {
        "group_id": "222",
        "visibility": "private",
        "event_apis": [],
    },
}

TG_LINK = {
    "id": 1,
    "og_title": "TG Meetup",
    "title": None,
    "og_description": None,
    "description": None,
    "og_image": None,
    "url": "https://example.com/tg-meetup",
    "event_starts_at": "2026-08-01T18:00:00Z",
    "event_location": "Some place",
    "group_id": "111",
}

LUMA_EVENT = {
    "id": "luma-abc123",
    "title": "Luma Event",
    "description": "",
    "image": None,
    "url": "https://luma.com/abc123",
    "starts_at": "2026-08-02T18:00:00Z",
    "ends_at": None,
    "location": None,
    "source": "luma",
    "community": "visible",
}


@pytest.fixture(autouse=True)
def stub_sources(monkeypatch):
    """Isolate the handler from real network/DB calls for Sources A and B."""
    monkeypatch.setattr(config, "get_all_event_groups", lambda: dict(GROUPS))
    monkeypatch.setattr(events_module, "get_event_links", lambda group_ids=None: [dict(TG_LINK)])
    monkeypatch.setattr(events_module, "enrich_event", lambda url: {})
    monkeypatch.setattr(
        events_module, "fetch_luma_events",
        lambda url, key, api_id=None: [dict(LUMA_EVENT)],
    )
    monkeypatch.setattr(events_module, "fetch_guildhost_events", lambda url, key: [])


def _invoke(path="/api/events", headers=None):
    """Build a handler instance and call do_GET without a real socket.

    BaseHTTPRequestHandler.__init__ normally drives the socket handshake, so
    we bypass it via __new__ and set only the attributes send_response /
    send_header / end_headers actually touch.
    """
    h = events_module.handler.__new__(events_module.handler)
    h.path = path
    h.headers = headers or {}
    h.client_address = ("127.0.0.1", 12345)
    h.request_version = "HTTP/1.1"
    h.requestline = f"GET {path} HTTP/1.1"
    h.rfile = io.BytesIO()
    h.wfile = io.BytesIO()
    h.do_GET()
    raw = h.wfile.getvalue()
    _, _, body = raw.partition(b"\r\n\r\n")
    return json.loads(body.decode())


class _FakeResponse:
    """Minimal stand-in for the urlopen() context manager."""

    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode()

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# --- handler-level tests -----------------------------------------------

def test_manual_event_in_visible_group_is_merged(monkeypatch):
    manual_event = {
        "id": "manual-1",
        "title": "Manual Meetup",
        "description": "",
        "image": None,
        "url": "https://example.com/manual-event",
        "starts_at": "2026-08-03T18:00:00Z",
        "ends_at": None,
        "location": "HQ",
        "source": "manual",
        "community": "visible",
    }
    monkeypatch.setattr(events_module, "_fetch_manual_events", lambda: [manual_event])

    body = _invoke()

    ids = {e["id"] for e in body["events"]}
    assert "manual-1" in ids
    merged = next(e for e in body["events"] if e["id"] == "manual-1")
    assert merged["source"] == "manual"
    assert merged["community"] == "visible"
    # Sources A and B are untouched by the additive merge.
    assert "tg-1" in ids
    assert "luma-abc123" in ids


def test_manual_event_in_non_visible_group_is_dropped(monkeypatch):
    hidden_events = [
        {  # private community — caller has no membership (no auth header)
            "id": "manual-private",
            "title": "Private Event",
            "url": "https://example.com/private-event",
            "starts_at": "2026-08-04T18:00:00Z",
            "ends_at": None,
            "location": None,
            "source": "manual",
            "community": "private",
        },
        {  # community key not present in config at all
            "id": "manual-unknown",
            "title": "Unknown Community Event",
            "url": "https://example.com/unknown-event",
            "starts_at": "2026-08-05T18:00:00Z",
            "ends_at": None,
            "location": None,
            "source": "manual",
            "community": "does-not-exist",
        },
    ]
    monkeypatch.setattr(events_module, "_fetch_manual_events", lambda: hidden_events)

    body = _invoke()

    ids = {e["id"] for e in body["events"]}
    assert "manual-private" not in ids
    assert "manual-unknown" not in ids
    # Telegram + Luma are unaffected by the drop.
    assert "tg-1" in ids
    assert "luma-abc123" in ids


def test_handler_degrades_gracefully_when_manual_fetch_fails(monkeypatch):
    """A real network failure inside _fetch_manual_events must never break
    the feed — Telegram + Luma results still come back, no exception."""
    monkeypatch.setattr(config, "CA_CONFIG_URL", "https://ca.example.com/api/config")
    monkeypatch.setattr(config, "CA_CONFIG_SECRET", "secret")

    def _raise(*args, **kwargs):
        raise urllib.error.URLError("boom")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)

    body = _invoke()

    sources = {e["source"] for e in body["events"]}
    assert "telegram" in sources
    assert "luma" in sources
    assert not any(e["source"] == "manual" for e in body["events"])


# --- _fetch_manual_events unit tests ------------------------------------

def test_fetch_manual_events_returns_empty_without_ca_config_url(monkeypatch):
    monkeypatch.setattr(config, "CA_CONFIG_URL", None)
    assert events_module._fetch_manual_events() == []


def test_fetch_manual_events_returns_empty_without_secret(monkeypatch):
    monkeypatch.setattr(config, "CA_CONFIG_URL", "https://ca.example.com/api/config")
    monkeypatch.setattr(config, "CA_CONFIG_SECRET", None)
    assert events_module._fetch_manual_events() == []


def test_fetch_manual_events_network_failure_returns_empty(monkeypatch):
    monkeypatch.setattr(config, "CA_CONFIG_URL", "https://ca.example.com/api/config")
    monkeypatch.setattr(config, "CA_CONFIG_SECRET", "secret")
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **kw: (_ for _ in ()).throw(urllib.error.URLError("boom")))

    assert events_module._fetch_manual_events() == []


def test_fetch_manual_events_malformed_payload_returns_empty(monkeypatch):
    monkeypatch.setattr(config, "CA_CONFIG_URL", "https://ca.example.com/api/config")
    monkeypatch.setattr(config, "CA_CONFIG_SECRET", "secret")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=5: _FakeResponse({"not_events": []}))

    assert events_module._fetch_manual_events() == []


def test_fetch_manual_events_parses_events_key(monkeypatch):
    monkeypatch.setattr(config, "CA_CONFIG_URL", "https://ca.example.com/api/config")
    monkeypatch.setattr(config, "CA_CONFIG_SECRET", "secret")
    payload = {"events": [{"id": "m1", "community": "visible"}]}
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=5: _FakeResponse(payload))

    assert events_module._fetch_manual_events() == payload["events"]
