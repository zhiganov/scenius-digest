import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (get from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Load groups configuration
GROUPS_FILE = Path(__file__).parent / "groups.json"

def load_groups():
    """Load monitored groups from JSON config file."""
    if GROUPS_FILE.exists():
        with open(GROUPS_FILE) as f:
            return json.load(f)

    # Fallback: build from legacy env vars for backward compatibility
    legacy_group_id = os.getenv("MONITOR_GROUP_ID")
    if legacy_group_id:
        return {
            "default": {
                "name": "Default Group",
                "group_id": legacy_group_id,
                "output_channel": os.getenv("DIGEST_CHANNEL_ID", "-1002708526104"),
                "topics": {
                    "links": os.getenv("TOPIC_LINKS_ID"),
                    "memes": os.getenv("TOPIC_MEMES_ID"),
                }
            }
        }

    return {}

MONITORED_GROUPS = load_groups()

def get_group_by_chat_id(chat_id: str) -> tuple[str, dict] | tuple[None, None]:
    """Find group config by chat ID. Returns (group_key, group_config) or (None, None)."""
    chat_id = str(chat_id)
    for key, config in MONITORED_GROUPS.items():
        if str(config.get("group_id")) == chat_id:
            return key, config
    return None, None

def get_topic_name(group_key: str, thread_id: str) -> str | None:
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

# Auto-post settings (disabled by default - use /export for Claude to generate)
AUTO_POST_ENABLED = os.getenv("AUTO_POST_ENABLED", "false").lower() == "true"

# Day of week to post digest (0 = Monday, 6 = Sunday)
DIGEST_DAY = int(os.getenv("DIGEST_DAY", "0"))  # Monday by default

# Hour to post digest (24h format, UTC)
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "9"))  # 9 AM UTC

# API server port (for Claude to fetch links)
API_PORT = int(os.getenv("API_PORT", "8080"))
