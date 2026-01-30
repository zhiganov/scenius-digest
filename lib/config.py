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

# Load groups configuration
# In Vercel, __file__ is in lib/, groups.json is in project root
GROUPS_FILE = Path(__file__).parent.parent / "groups.json"


def load_groups():
    """Load monitored groups from JSON config file."""
    if GROUPS_FILE.exists():
        with open(GROUPS_FILE) as f:
            return json.load(f)
    return {}


MONITORED_GROUPS = load_groups()


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
