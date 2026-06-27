import os
import json
import time
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (get from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Webhook secret for verifying Telegram requests
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# community-admin config seam (community-admin#... / V2). When set, group config
# is read from community-admin's GET /api/config; otherwise (and on any failure)
# we fall back to the static groups.json. groups.json stays in the repo as the
# fallback so this is zero-disruption.
CA_CONFIG_URL = os.getenv("CA_CONFIG_URL")
CA_CONFIG_SECRET = os.getenv("CA_CONFIG_SECRET")

# In Vercel, __file__ is in lib/, JSON configs are in project root
_PROJECT_ROOT = Path(__file__).parent.parent

# groups.json — Telegram-based communities (webhook, link collection, digests).
# Now the FALLBACK source; community-admin /api/config is primary when configured.
GROUPS_FILE = _PROJECT_ROOT / "groups.json"

# event_sources.json — non-Telegram communities with external event APIs only.
# Still static (event-only communities are not yet served via the config seam).
EVENT_SOURCES_FILE = _PROJECT_ROOT / "event_sources.json"


def _load_json(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


_CONFIG_CACHE = {"data": None, "ts": 0.0}
_CONFIG_TTL = 60  # seconds


def fetch_config() -> dict:
    """Telegram-community config, in groups.json dict shape.

    Reads from community-admin's GET /api/config (Bearer auth) with a 60s TTL
    cache, falling back to the static groups.json on any error or when the
    integration env vars are unset. Returns the same shape MONITORED_GROUPS
    always had, so all consumers work unchanged.
    """
    now = time.time()
    if _CONFIG_CACHE["data"] is not None and (now - _CONFIG_CACHE["ts"]) < _CONFIG_TTL:
        return _CONFIG_CACHE["data"]

    data = None
    if CA_CONFIG_URL and CA_CONFIG_SECRET:
        try:
            req = urllib.request.Request(
                CA_CONFIG_URL,
                headers={"Authorization": f"Bearer {CA_CONFIG_SECRET}"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode())
            candidate = payload.get("communities", payload)
            if isinstance(candidate, dict) and candidate:
                data = candidate
        except Exception as e:
            print(f"[config] /api/config fetch failed, using groups.json: {e}")

    if data is None:
        data = _load_json(GROUPS_FILE)

    _CONFIG_CACHE["data"] = data
    _CONFIG_CACHE["ts"] = now
    return data


def __getattr__(name):
    # PEP 562: expose MONITORED_GROUPS as a dynamic, cached fetch so every
    # `config.MONITORED_GROUPS` reader picks up live config without code changes.
    if name == "MONITORED_GROUPS":
        return fetch_config()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


EVENT_SOURCES = _load_json(EVENT_SOURCES_FILE)


def get_group_by_chat_id(chat_id: str) -> tuple[str, dict] | tuple[None, None]:
    """Find group config by chat ID. Returns (group_key, group_config) or (None, None)."""
    chat_id = str(chat_id)
    for key, cfg in fetch_config().items():
        if str(cfg.get("group_id")) == chat_id:
            return key, cfg
    return None, None


def get_topic_name(group_key: str, thread_id) -> str | None:
    """Get topic name for a thread ID within a specific group."""
    groups = fetch_config()
    if group_key not in groups:
        return None
    topics = groups[group_key].get("topics", {})
    thread_id = str(thread_id) if thread_id else None
    for name, tid in topics.items():
        if str(tid) == thread_id:
            return name
    return None


def get_all_group_ids() -> list[str]:
    """Get list of all monitored group IDs."""
    return [str(g.get("group_id")) for g in fetch_config().values()]


def is_event_topic(group_key: str, topic_name: str) -> bool:
    """Check if a topic is in the group's event_topics list."""
    groups = fetch_config()
    if group_key not in groups:
        return False
    event_topics = groups[group_key].get("event_topics", [])
    return topic_name in event_topics


def get_groups_by_city(city: str) -> dict:
    """Return all groups matching a city slug."""
    return {
        key: cfg for key, cfg in fetch_config().items()
        if cfg.get("city") == city
    }


def get_all_event_groups() -> dict:
    """Return all communities with event sources (groups + event_sources)."""
    merged = dict(fetch_config())
    merged.update(EVENT_SOURCES)
    return merged


def get_event_groups_by_city(city: str) -> dict:
    """Return all communities matching a city slug (groups + event_sources)."""
    return {
        key: cfg for key, cfg in get_all_event_groups().items()
        if cfg.get("city") == city
    }


def visible_groups(groups: dict, member_ids: set[str] | None = None) -> dict:
    """Filter a {key: cfg} dict to communities the caller may see.

    Public communities (visibility != 'private', or no visibility field) are
    always included. A private community is included only if its id - the dict
    key, which is the community-admin community id from /api/config - is in
    `member_ids`, the stringified community ids from the caller's verified token
    (auth.member_ids_from_request). Membership now travels in tokens, not config.
    """
    member_ids = member_ids or set()
    return {
        k: v for k, v in groups.items()
        if v.get("visibility") != "private" or str(k) in member_ids
    }
