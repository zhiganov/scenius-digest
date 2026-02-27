import os
import json
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

# In Vercel, __file__ is in lib/, JSON configs are in project root
_PROJECT_ROOT = Path(__file__).parent.parent

# groups.json — Telegram-based communities (webhook, link collection, digests)
GROUPS_FILE = _PROJECT_ROOT / "groups.json"

# event_sources.json — non-Telegram communities with external event APIs only
# These are managed by community-admin (once built); this file is interim.
EVENT_SOURCES_FILE = _PROJECT_ROOT / "event_sources.json"


def _load_json(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


MONITORED_GROUPS = _load_json(GROUPS_FILE)
EVENT_SOURCES = _load_json(EVENT_SOURCES_FILE)


def get_group_by_chat_id(chat_id: str) -> tuple[str, dict] | tuple[None, None]:
    """Find group config by chat ID. Returns (group_key, group_config) or (None, None)."""
    chat_id = str(chat_id)
    for key, config in MONITORED_GROUPS.items():
        if str(config.get("group_id")) == chat_id:
            return key, config
    return None, None


def get_topic_name(group_key: str, thread_id) -> str | None:
    """Get topic name for a thread ID within a specific group."""
    if group_key not in MONITORED_GROUPS:
        return None
    topics = MONITORED_GROUPS[group_key].get("topics", {})
    thread_id = str(thread_id) if thread_id else None
    for name, tid in topics.items():
        if str(tid) == thread_id:
            return name
    return None


def get_all_group_ids() -> list[str]:
    """Get list of all monitored group IDs."""
    return [str(g.get("group_id")) for g in MONITORED_GROUPS.values()]


def is_event_topic(group_key: str, topic_name: str) -> bool:
    """Check if a topic is in the group's event_topics list."""
    if group_key not in MONITORED_GROUPS:
        return False
    event_topics = MONITORED_GROUPS[group_key].get("event_topics", [])
    return topic_name in event_topics


def get_groups_by_city(city: str) -> dict:
    """Return all groups matching a city slug."""
    return {
        key: cfg for key, cfg in MONITORED_GROUPS.items()
        if cfg.get("city") == city
    }


def get_all_event_groups() -> dict:
    """Return all communities with event sources (groups + event_sources)."""
    merged = dict(MONITORED_GROUPS)
    merged.update(EVENT_SOURCES)
    return merged


def get_event_groups_by_city(city: str) -> dict:
    """Return all communities matching a city slug (groups + event_sources)."""
    return {
        key: cfg for key, cfg in get_all_event_groups().items()
        if cfg.get("city") == city
    }
