# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Scenius Digest publishes curated highlights from the Sensemaking Scenius community to the [@scenius](https://t.me/scenius) Telegram channel. Two types of content:

1. **Meeting digests** - Narrative summaries of biweekly Scenius calls (from Fireflies.ai)
2. **Weekly links roundup** - Curated links from community Telegram topics (from bot API)

## Architecture

```
Zoom Meetings ──► Fireflies.ai ──┐
                                 ├──► Claude Code ──► @scenius channel
Telegram Group ──► Bot (Fly.io) ─┘
```

**Bot components** (`bot/`):
- `bot.py` - Main entry: Telegram handlers + aiohttp API server (runs concurrently)
- `database.py` - SQLite storage with `links` table (URL, topic, shared_by, message_text)
- `config.py` - Environment variables (BOT_TOKEN, MONITOR_GROUP_ID, TOPIC_*_ID)
- `digest.py` - Basic digest formatting (Claude generates better narratives)

**Slash commands** (`.claude/commands/`):
- `digest-links.md` - Weekly links roundup workflow
- `digest-meeting.md` - Meeting digest workflow

## Development Commands

```bash
# Bot development
cd bot
pip install -r requirements.txt
cp .env.example .env  # then fill in values
python bot.py

# Deploy to Fly.io
fly deploy
fly logs              # check logs
fly secrets list      # view configured secrets
```

## Bot API

Deployed at `https://scenius-digest-bot.fly.dev`:

| Endpoint | Description |
|----------|-------------|
| `GET /api/links` | Unpublished links (JSON) |
| `GET /api/links?days=14` | Links from last N days |
| `POST /api/mark-published` | Mark as published: `{"ids": [1,2,3]}` |
| `GET /health` | Health check |

Response includes `message_text` field with original sharer's commentary.

## MCP Integrations

- **Fireflies MCP** - Meeting transcripts (filter: `keyword:"scenius" scope:title`)
- **Firecrawl MCP** - Scrape link content for digest summaries

## Posting to Telegram

Use the bot's API token directly:

```bash
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "-1002708526104", "text": "Your message", "disable_web_page_preview": true}'
```

BOT_TOKEN is stored as a Fly.io secret.

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

| Resource | Value |
|----------|-------|
| Channel | @scenius |
| Channel Chat ID | -1002708526104 |
| Bot | @sensemaking_bot |
| Monitored Group | -1002141367711 |
| Links Topic ID | 230 |
| Memes Topic ID | 4605 |
