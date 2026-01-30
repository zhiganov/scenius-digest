import json
import os
import re
import logging
from http.server import BaseHTTPRequestHandler

# Add project root to path for lib imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import config
from lib.database import add_link, get_stats
from lib.telegram import send_message

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*')


def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    return URL_PATTERN.findall(text)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Verify webhook secret
        secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if config.WEBHOOK_SECRET and secret != config.WEBHOOK_SECRET:
            self.send_response(403)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        update = json.loads(body)

        try:
            self._handle_update(update)
        except Exception as e:
            logger.error(f"Error handling update: {e}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def _handle_update(self, update: dict):
        message = update.get("message")
        if not message:
            return

        text = message.get("text") or message.get("caption") or ""
        chat_id = str(message["chat"]["id"])

        # Handle bot commands
        if text.startswith("/"):
            self._handle_command(message, text, chat_id)
            return

        # Check if from monitored group
        group_key, group_config = config.get_group_by_chat_id(chat_id)
        if not group_key:
            return

        # Check if from monitored topic
        topic_id = message.get("message_thread_id")
        topic_name = config.get_topic_name(group_key, topic_id)
        if not topic_name:
            return

        # Extract URLs
        urls = extract_urls(text)
        if not urls:
            return

        # Get sender info
        user = message.get("from", {})
        shared_by = user.get("username") or user.get("first_name")

        group_id = group_config.get("group_id")
        group_name = group_config.get("name", group_key)

        for url in urls:
            added = add_link(
                url=url,
                topic=topic_name,
                shared_by=shared_by,
                message_id=message.get("message_id"),
                message_text=text,
                group_id=group_id,
                group_name=group_name,
            )
            if added:
                logger.info(f"[{group_name}] Stored link from {shared_by} in {topic_name}: {url}")

    def _handle_command(self, message: dict, text: str, chat_id: str):
        parts = text.split()
        command = parts[0].split("@")[0].lower()  # strip @botname

        if command == "/debug":
            topic_id = message.get("message_thread_id")
            group_key, _ = config.get_group_by_chat_id(chat_id)
            monitored = f"✅ Monitored as '{group_key}'" if group_key else "❌ Not monitored"
            groups_list = "\n".join([
                f"  • {k}: {v.get('name', k)} (ID: {v.get('group_id')})"
                for k, v in config.MONITORED_GROUPS.items()
            ])
            send_message(chat_id, (
                f"🔧 Debug info:\n"
                f"• Chat ID: {chat_id}\n"
                f"• Topic/Thread ID: {topic_id}\n"
                f"• Chat type: {message['chat'].get('type')}\n"
                f"• Status: {monitored}\n\n"
                f"📋 Monitored groups:\n{groups_list or '  (none configured)'}"
            ))

        elif command == "/stats":
            arg = parts[1] if len(parts) > 1 else None
            if arg and arg in config.MONITORED_GROUPS:
                gc = config.MONITORED_GROUPS[arg]
                stats = get_stats(group_id=gc.get("group_id"))
                send_message(chat_id, (
                    f"📊 Stats for {gc.get('name', arg)}:\n"
                    f"• Total: {stats['total']}\n"
                    f"• Unpublished: {stats['unpublished']}\n"
                    f"• Published: {stats['published']}"
                ))
            else:
                lines = ["📊 Stats by group:\n"]
                total_stats = {"total": 0, "unpublished": 0, "published": 0}
                for key, gc in config.MONITORED_GROUPS.items():
                    stats = get_stats(group_id=gc.get("group_id"))
                    lines.append(f"**{gc.get('name', key)}**")
                    lines.append(f"  • Unpublished: {stats['unpublished']}")
                    lines.append(f"  • Published: {stats['published']}")
                    total_stats["total"] += stats["total"]
                    total_stats["unpublished"] += stats["unpublished"]
                    total_stats["published"] += stats["published"]
                lines.append(f"\n**Total**: {total_stats['unpublished']} unpublished, {total_stats['published']} published")
                send_message(chat_id, "\n".join(lines))

        elif command == "/groups":
            lines = ["📋 Configured groups:\n"]
            for key, gc in config.MONITORED_GROUPS.items():
                name = gc.get("name", key)
                group_id = gc.get("group_id")
                output = gc.get("output_channel", "not set")
                topics = gc.get("topics", {})
                topics_str = ", ".join(f"{k}={v}" for k, v in topics.items())
                lines.append(f"**{key}** ({name})")
                lines.append(f"  Group ID: {group_id}")
                lines.append(f"  Output: {output}")
                lines.append(f"  Topics: {topics_str}")
                lines.append("")
            send_message(chat_id, "\n".join(lines))

        elif command == "/digest":
            from lib.digest import generate_weekly_digest
            from lib.database import mark_as_published

            arg = parts[1] if len(parts) > 1 else None
            if arg and arg in config.MONITORED_GROUPS:
                groups_to_process = {arg: config.MONITORED_GROUPS[arg]}
            else:
                groups_to_process = config.MONITORED_GROUPS

            for key, gc in groups_to_process.items():
                group_id = gc.get("group_id")
                output_channel = gc.get("output_channel")
                group_name = gc.get("name", key)
                if not output_channel:
                    continue
                msg, link_ids = generate_weekly_digest(group_id=group_id, group_name=group_name)
                if msg:
                    send_message(output_channel, msg)
                    mark_as_published(link_ids)

            send_message(chat_id, f"Digest posted for: {arg or 'all groups'}")
