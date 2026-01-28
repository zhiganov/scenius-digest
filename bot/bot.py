#!/usr/bin/env python3
"""
Scenius Links Monitor Bot

Monitors Telegram groups for links shared in specific topics.
Exposes an API for Claude to fetch collected links.
Supports multiple groups with per-group output channels.
"""

import re
import json
import asyncio
import logging
from datetime import time
from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

import config
from database import add_link, get_unpublished_links, mark_as_published, get_stats
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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and extract links."""
    message = update.message

    if not message:
        return

    # Check if from any monitored group
    chat_id = str(message.chat.id)
    group_key, group_config = config.get_group_by_chat_id(chat_id)

    if not group_key:
        return  # Not from a monitored group

    # Check if from monitored topic (forum thread)
    topic_id = message.message_thread_id
    topic_name = config.get_topic_name(group_key, topic_id)

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

    # Store each URL with group info
    group_id = group_config.get("group_id")
    group_name = group_config.get("name", group_key)

    for url in urls:
        added = add_link(
            url=url,
            topic=topic_name,
            shared_by=shared_by,
            message_id=message.message_id,
            message_text=text,
            group_id=group_id,
            group_name=group_name
        )
        if added:
            logger.info(f"[{group_name}] Stored link from {shared_by} in {topic_name}: {url}")


async def post_digest(context: ContextTypes.DEFAULT_TYPE, group_key: str = None):
    """Generate and post weekly digest for a specific group or all groups."""
    if group_key and group_key in config.MONITORED_GROUPS:
        groups_to_process = {group_key: config.MONITORED_GROUPS[group_key]}
    else:
        groups_to_process = config.MONITORED_GROUPS

    for key, group_config in groups_to_process.items():
        group_id = group_config.get("group_id")
        output_channel = group_config.get("output_channel")
        group_name = group_config.get("name", key)

        if not output_channel:
            logger.warning(f"[{group_name}] No output_channel configured, skipping")
            continue

        logger.info(f"[{group_name}] Generating weekly digest...")

        message, link_ids = generate_weekly_digest(group_id=group_id, group_name=group_name)

        if not message:
            logger.info(f"[{group_name}] No links to include in digest")
            continue

        try:
            await context.bot.send_message(
                chat_id=output_channel,
                text=message,
                disable_web_page_preview=True
            )
            mark_as_published(link_ids)
            logger.info(f"[{group_name}] Posted digest with {len(link_ids)} links to {output_channel}")
        except Exception as e:
            logger.error(f"[{group_name}] Failed to post digest: {e}")


async def cmd_digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual command to post digest. Usage: /digest [group_key]"""
    user = update.effective_user
    args = context.args

    group_key = args[0] if args else None
    logger.info(f"Manual digest requested by {user.username} for group: {group_key or 'all'}")

    await post_digest(context, group_key=group_key)
    await update.message.reply_text(f"Digest posted for: {group_key or 'all groups'}")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current stats. Usage: /stats [group_key]"""
    args = context.args
    group_key = args[0] if args else None

    if group_key and group_key in config.MONITORED_GROUPS:
        group_config = config.MONITORED_GROUPS[group_key]
        group_id = group_config.get("group_id")
        stats = get_stats(group_id=group_id)
        await update.message.reply_text(
            f"📊 Stats for {group_config.get('name', group_key)}:\n"
            f"• Total: {stats['total']}\n"
            f"• Unpublished: {stats['unpublished']}\n"
            f"• Published: {stats['published']}"
        )
    else:
        # Show stats for all groups
        lines = ["📊 Stats by group:\n"]
        total_stats = {"total": 0, "unpublished": 0, "published": 0}

        for key, group_config in config.MONITORED_GROUPS.items():
            group_id = group_config.get("group_id")
            stats = get_stats(group_id=group_id)
            lines.append(f"**{group_config.get('name', key)}**")
            lines.append(f"  • Unpublished: {stats['unpublished']}")
            lines.append(f"  • Published: {stats['published']}")
            total_stats["total"] += stats["total"]
            total_stats["unpublished"] += stats["unpublished"]
            total_stats["published"] += stats["published"]

        lines.append(f"\n**Total**: {total_stats['unpublished']} unpublished, {total_stats['published']} published")
        await update.message.reply_text("\n".join(lines))


async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to show chat/topic IDs and monitored groups."""
    message = update.message
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    # Check if this chat is monitored
    group_key, group_config = config.get_group_by_chat_id(str(chat_id))
    monitored_status = f"✅ Monitored as '{group_key}'" if group_key else "❌ Not monitored"

    # List all monitored groups
    groups_list = "\n".join([
        f"  • {k}: {v.get('name', k)} (ID: {v.get('group_id')})"
        for k, v in config.MONITORED_GROUPS.items()
    ])

    await message.reply_text(
        f"🔧 Debug info:\n"
        f"• Chat ID: {chat_id}\n"
        f"• Topic/Thread ID: {topic_id}\n"
        f"• Chat type: {message.chat.type}\n"
        f"• Status: {monitored_status}\n\n"
        f"📋 Monitored groups:\n{groups_list or '  (none configured)'}"
    )


async def cmd_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all monitored groups and their output channels."""
    lines = ["📋 Configured groups:\n"]

    for key, group_config in config.MONITORED_GROUPS.items():
        name = group_config.get("name", key)
        group_id = group_config.get("group_id")
        output = group_config.get("output_channel", "not set")
        topics = group_config.get("topics", {})
        topics_str = ", ".join(f"{k}={v}" for k, v in topics.items())

        lines.append(f"**{key}** ({name})")
        lines.append(f"  Group ID: {group_id}")
        lines.append(f"  Output: {output}")
        lines.append(f"  Topics: {topics_str}")
        lines.append("")

    await update.message.reply_text("\n".join(lines))


# --- HTTP API for Claude ---

async def api_links(request):
    """Return collected links as JSON for Claude to fetch."""
    days = int(request.query.get("days", 7))
    group = request.query.get("group")  # group key or group_id

    # Resolve group to group_id
    group_id = None
    if group:
        if group in config.MONITORED_GROUPS:
            group_id = config.MONITORED_GROUPS[group].get("group_id")
        else:
            # Assume it's a group_id directly
            group_id = group

    links = get_unpublished_links(since_days=days, group_id=group_id)

    # Build response
    response = {
        "links": links,
        "count": len(links),
        "topics": {
            "links": len([l for l in links if l["topic"] == "links"]),
            "memes": len([l for l in links if l["topic"] == "memes"]),
        }
    }

    if group_id:
        response["group_id"] = group_id
    else:
        # Include breakdown by group when fetching all
        by_group = {}
        for link in links:
            gname = link.get("group_name") or "unknown"
            by_group[gname] = by_group.get(gname, 0) + 1
        response["by_group"] = by_group

    return web.json_response(response)


async def api_groups(request):
    """Return configured groups."""
    groups = {}
    for key, cfg in config.MONITORED_GROUPS.items():
        groups[key] = {
            "name": cfg.get("name", key),
            "group_id": cfg.get("group_id"),
            "output_channel": cfg.get("output_channel"),
            "topics": list(cfg.get("topics", {}).keys())
        }
    return web.json_response({"groups": groups})


async def api_mark_published(request):
    """Mark links as published after digest is posted."""
    try:
        data = await request.json()
        link_ids = data.get("ids", [])
        if link_ids:
            mark_as_published(link_ids)
            return web.json_response({"status": "ok", "marked": len(link_ids)})
        return web.json_response({"status": "ok", "marked": 0})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)


async def api_health(request):
    """Health check endpoint."""
    return web.json_response({
        "status": "healthy",
        "groups": len(config.MONITORED_GROUPS)
    })


def create_api_app():
    """Create the aiohttp web application."""
    app = web.Application()
    app.router.add_get("/api/links", api_links)
    app.router.add_get("/api/groups", api_groups)
    app.router.add_post("/api/mark-published", api_mark_published)
    app.router.add_get("/health", api_health)
    app.router.add_get("/", api_health)
    return app


async def run_api_server():
    """Run the HTTP API server."""
    app = create_api_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.API_PORT)
    await site.start()
    logger.info(f"API server running on port {config.API_PORT}")


async def main_async():
    """Run both Telegram bot and API server."""
    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in environment")

    # Log configured groups
    logger.info(f"Monitoring {len(config.MONITORED_GROUPS)} groups:")
    for key, cfg in config.MONITORED_GROUPS.items():
        logger.info(f"  - {key}: {cfg.get('name')} -> {cfg.get('output_channel')}")

    # Start API server
    await run_api_server()

    # Create Telegram application
    app = Application.builder().token(config.BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("debug", cmd_debug))
    app.add_handler(CommandHandler("groups", cmd_groups))
    app.add_handler(MessageHandler(
        filters.TEXT | filters.CAPTION,
        handle_message
    ))

    # Schedule weekly digest (optional - disabled by default)
    if config.AUTO_POST_ENABLED:
        job_queue = app.job_queue
        job_queue.run_daily(
            lambda ctx: post_digest(ctx, group_key=None),  # Post for all groups
            time=time(hour=config.DIGEST_HOUR, minute=0),
            days=(config.DIGEST_DAY,)
        )
        logger.info(f"Auto-post enabled for day {config.DIGEST_DAY} at {config.DIGEST_HOUR}:00 UTC")

    # Start polling (this runs forever)
    logger.info("Bot started. API available at /api/links")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Keep running
    while True:
        await asyncio.sleep(3600)


def main():
    """Entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
