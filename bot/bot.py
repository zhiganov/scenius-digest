#!/usr/bin/env python3
"""
Scenius Links Monitor Bot

Monitors a Telegram group for links shared in specific topics
and posts weekly digests to the @scenius channel.
"""

import re
import logging
from datetime import time
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

import config
from database import add_link, get_unpublished_links, mark_as_published
from digest import generate_weekly_digest

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL regex pattern
URL_PATTERN = re.compile(
    r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
)


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from text."""
    if not text:
        return []
    return URL_PATTERN.findall(text)


def get_topic_name(topic_id: str) -> str | None:
    """Map topic ID to topic name."""
    for name, tid in config.MONITORED_TOPICS.items():
        if str(tid) == str(topic_id):
            return name
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and extract links."""
    message = update.message

    if not message:
        return

    # Check if from monitored group
    if str(message.chat.id) != str(config.MONITOR_GROUP_ID):
        return

    # Check if from monitored topic (forum thread)
    topic_id = message.message_thread_id
    topic_name = get_topic_name(topic_id)

    if not topic_name:
        return  # Not a monitored topic

    # Extract URLs from message
    text = message.text or message.caption or ""
    urls = extract_urls(text)

    if not urls:
        return

    # Get sender info
    user = message.from_user
    shared_by = user.username or user.first_name if user else None

    # Store each URL
    for url in urls:
        added = add_link(
            url=url,
            topic=topic_name,
            shared_by=shared_by,
            message_id=message.message_id
        )
        if added:
            logger.info(f"Stored link from {shared_by} in {topic_name}: {url}")


async def post_digest(context: ContextTypes.DEFAULT_TYPE):
    """Generate and post weekly digest."""
    logger.info("Generating weekly digest...")

    message, link_ids = generate_weekly_digest()

    if not message:
        logger.info("No links to include in digest")
        return

    try:
        await context.bot.send_message(
            chat_id=config.DIGEST_CHANNEL_ID,
            text=message,
            disable_web_page_preview=True
        )
        mark_as_published(link_ids)
        logger.info(f"Posted digest with {len(link_ids)} links")
    except Exception as e:
        logger.error(f"Failed to post digest: {e}")


async def cmd_digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual command to post digest (for testing)."""
    user = update.effective_user
    logger.info(f"Manual digest requested by {user.username}")

    await post_digest(context)
    await update.message.reply_text("Digest posted!")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current stats."""
    links = get_unpublished_links(since_days=7)
    links_count = len([l for l in links if l["topic"] == "links"])
    memes_count = len([l for l in links if l["topic"] == "memes"])

    await update.message.reply_text(
        f"📊 Current week stats:\n"
        f"• Links: {links_count}\n"
        f"• Memes: {memes_count}\n"
        f"• Total unpublished: {len(links)}"
    )


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export collected links for Claude to generate digest."""
    links = get_unpublished_links(since_days=7)

    if not links:
        await update.message.reply_text("No links collected this week.")
        return

    # Format for easy copy-paste to Claude
    lines = ["📋 Links collected this week:", ""]

    # Group by topic
    links_topic = [l for l in links if l["topic"] == "links"]
    memes_topic = [l for l in links if l["topic"] == "memes"]

    if links_topic:
        lines.append("📚 From Links topic:")
        for link in links_topic:
            shared_by = f" (by @{link['shared_by']})" if link["shared_by"] else ""
            lines.append(f"• {link['url']}{shared_by}")
        lines.append("")

    if memes_topic:
        lines.append("🎭 From Memes & Delight:")
        for link in memes_topic:
            shared_by = f" (by @{link['shared_by']})" if link["shared_by"] else ""
            lines.append(f"• {link['url']}{shared_by}")
        lines.append("")

    lines.append(f"Total: {len(links)} links")
    lines.append("")
    lines.append("Copy this to Claude to generate the weekly digest!")

    await update.message.reply_text("\n".join(lines), disable_web_page_preview=True)


async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to show chat/topic IDs."""
    message = update.message
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    await message.reply_text(
        f"🔧 Debug info:\n"
        f"• Chat ID: {chat_id}\n"
        f"• Topic/Thread ID: {topic_id}\n"
        f"• Chat type: {message.chat.type}"
    )


def main():
    """Start the bot."""
    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in environment")

    # Create application
    app = Application.builder().token(config.BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("debug", cmd_debug))
    app.add_handler(MessageHandler(
        filters.TEXT | filters.CAPTION,
        handle_message
    ))

    # Schedule weekly digest (optional - disabled by default)
    if config.AUTO_POST_ENABLED:
        job_queue = app.job_queue
        job_queue.run_daily(
            post_digest,
            time=time(hour=config.DIGEST_HOUR, minute=0),
            days=(config.DIGEST_DAY,)
        )
        logger.info(f"Auto-post enabled for day {config.DIGEST_DAY} at {config.DIGEST_HOUR}:00 UTC")
    else:
        logger.info("Auto-post disabled. Use /export to get links for Claude.")

    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
