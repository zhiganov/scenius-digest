# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Scenius Digest publishes curated highlights from the Sensemaking Scenius community to the [@scenius](https://t.me/scenius) Telegram channel. Two types of content:

1. **Meeting digests** - Narrative summaries of biweekly Scenius calls (from Fireflies.ai)
2. **Weekly links roundup** - Curated links from community Telegram topics (from bot API)

## Architecture

```
Fireflies.ai ──► Claude Code ──┐
                               ├──► @scenius Telegram channel
Telegram Group ──► Bot (Fly.io) ┘
```

- **bot/** - Python Telegram bot that monitors group topics and exposes API
- **.claude/commands/** - Slash commands for digest generation

## Development Commands

```bash
# Bot development
cd bot
pip install -r requirements.txt
python bot.py

# Deploy to Fly.io
cd bot
fly deploy

# Check logs
fly logs
```

## Bot API

When deployed at `https://scenius-digest-bot.fly.dev`:

- `GET /api/links` - Collected links (JSON)
- `GET /api/links?days=14` - Links from last N days
- `POST /api/mark-published` - Mark as published: `{"ids": [1,2,3]}`

## MCP Integrations Required

- **Fireflies MCP** - Meeting transcripts (filter: `keyword:"scenius" scope:title`)

## Posting to Telegram

Use the bot's API token directly via curl:

```bash
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "-1002708526104", "text": "Your message", "disable_web_page_preview": true}'
```

The bot token is stored as a Fly.io secret. For local testing, use `fly secrets list` or set BOT_TOKEN in .env.

---

## Digest Generation Instructions

### Meeting Digests

Source: Fireflies.ai transcripts filtered by `keyword:"scenius" scope:title`

Format:
```
📋 [Meeting Title] Digest
🗓 [Date] • ⏱ [Duration] min

[Engaging narrative paragraphs - tell the story of what was discussed. Highlight interesting ideas, projects, insights. Conversational tone. Include specific details - numbers, project names, concepts.]

[Second paragraph diving into highlights that would interest people outside the community.]
```

### Weekly Links Roundup

Source: `GET https://scenius-digest-bot.fly.dev/api/links`

Workflow:
1. Fetch links from API
2. Fetch each URL to understand content
3. Generate narrative digest
4. Post to @scenius (chat_id: -1002708526104)
5. Mark links as published via API

Format:
```
🔗 Weekly Links Roundup
🗓 Week of [Date]

[Opening sentence about what the community explored this week.]

📚 Worth Reading

[1-2 sentence description per link - why it's interesting, why it matters]

• [Title] - [URL]

🎭 Memes & Delight

[Brief fun intro]

• [URL]

[Closing line inviting people to join]
```

### Writing Style

- Narrative and engaging, not bullet points
- Highlight interesting/novel ideas
- Specific details (numbers, names, concepts)
- Conversational tone for Telegram
- Credit sharers when relevant (e.g., "via @username")

### What NOT to Include

- Action items or internal task assignments
- Internal governance details
- Sensitive/private discussions
- Broken links
- Transcript links (require login)

## Telegram

- Channel: @scenius
- Chat ID: -1002708526104
- Bot: @sensemaking_bot
