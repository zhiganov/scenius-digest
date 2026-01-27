import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (get from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Group to monitor (get after adding bot to group)
MONITOR_GROUP_ID = os.getenv("MONITOR_GROUP_ID")

# Channel to post digests to
DIGEST_CHANNEL_ID = os.getenv("DIGEST_CHANNEL_ID", "-1002708526104")  # @scenius

# Topic IDs to monitor (get from group settings or message_thread_id)
# You'll need to update these after identifying the correct topic IDs
MONITORED_TOPICS = {
    "links": os.getenv("TOPIC_LINKS_ID"),
    "memes": os.getenv("TOPIC_MEMES_ID"),
}

# Day of week to post digest (0 = Monday, 6 = Sunday)
DIGEST_DAY = int(os.getenv("DIGEST_DAY", "0"))  # Monday by default

# Hour to post digest (24h format, UTC)
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "9"))  # 9 AM UTC
