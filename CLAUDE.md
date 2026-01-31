# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-community digest bot that collects links from Telegram groups and publishes curated digests to their respective channels.

**Supported communities:**
- **Sensemaking Scenius** → @scenius channel
- **Citizen Infra Builders** → [@citizen_infra](https://t.me/citizen_infra) channel

Two types of content:
1. **Meeting digests** - Narrative summaries of Zoom calls (transcripts via Fireflies.ai)
2. **Weekly links roundup** - Curated links from community Telegram topics (from bot API)

## Architecture

```
Telegram Groups ──► Webhook (Vercel) ──► Supabase ──► Claude Code ──► Output Channels
                                                           │
Zoom Meetings ──► Fireflies.ai ────────────────────────────┘
```

**Serverless functions** (`api/`):
- `api/webhook.py` - Telegram webhook handler (receives messages, stores links)
- `api/links.py` - GET unpublished links for digest generation
- `api/groups.py` - GET configured groups
- `api/mark_published.py` - POST mark links as published
- `api/health.py` - GET health check

**Shared modules** (`lib/`):
- `lib/config.py` - Env vars + groups.json loading
- `lib/database.py` - Supabase client (`digest_links` table)
- `lib/digest.py` - Digest formatting
- `lib/telegram.py` - Telegram Bot API helper (sendMessage via urllib)

**Slash commands** (`.claude/commands/`):
- `digest-links.md` - Weekly links roundup workflow (supports group argument)
- `digest-meeting.md` - Meeting digest workflow

**Legacy** (`bot/`): Original Fly.io bot (python-telegram-bot + SQLite + aiohttp). Kept for reference only — not deployed.

## Multi-Group Configuration

Groups are defined in `groups.json` (project root):

```json
{
  "scenius": {
    "name": "Sensemaking Scenius",
    "group_id": "-1002141367711",
    "output_channel": "-1002708526104",
    "topics": { "links": "230", "memes": "4605" }
  },
  "cibc": {
    "name": "Citizen Infra Builders",
    "group_id": "-1003188266615",
    "output_channel": "-1001800461815",
    "topics": { "news": "11", "resources": "266" }
  }
}
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (see .env.example)
cp .env.example .env

# Deploy to Vercel
vercel --prod

# Set env vars in Vercel
vercel env add BOT_TOKEN
vercel env add WEBHOOK_SECRET
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY
```

### Webhook Registration

```bash
# Delete old polling connection
curl "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook"

# Register webhook
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://scenius-digest.vercel.app/api/webhook","secret_token":"YOUR_SECRET","allowed_updates":["message"]}'
```

## Bot API

Deployed at `https://scenius-digest.vercel.app`:

| Endpoint | Description |
|----------|-------------|
| `GET /api/links` | All unpublished links |
| `GET /api/links?group=cibc` | Links from specific group |
| `GET /api/links?days=14` | Links from last N days |
| `GET /api/groups` | List configured groups |
| `POST /api/mark-published` | Mark as published: `{"ids": [1,2,3]}` |
| `GET /api/health` | Health check |

Response includes `group_id`, `group_name`, and `message_text` fields.

## Bot Commands

Send these in a monitored Telegram group:

| Command | Description |
|---------|-------------|
| `/debug` | Show chat/topic IDs, check if monitored |
| `/groups` | List all configured groups |
| `/stats [group]` | Show link statistics |
| `/digest [group]` | Post digest for group |

## Database

Uses `digest_links` table in the scenius-digest Supabase project. Schema:

```sql
CREATE TABLE digest_links (
  id BIGSERIAL PRIMARY KEY,
  url TEXT NOT NULL,
  title TEXT,
  description TEXT,
  group_id TEXT,
  group_name TEXT,
  topic TEXT NOT NULL,
  shared_by TEXT,
  shared_at TIMESTAMPTZ DEFAULT NOW(),
  message_id BIGINT,
  message_text TEXT,
  published BOOLEAN DEFAULT FALSE
);
```

## MCP Integrations

- **Fireflies MCP** - Meeting transcripts (filter: `keyword:"scenius" scope:title`)
- **Firecrawl MCP** - Scrape link content for digest summaries

## Posting to Telegram

Use the bot's API token directly:

```bash
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "{output_channel}", "text": "...", "disable_web_page_preview": true}'
```

BOT_TOKEN is stored as a Vercel environment variable.

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

Source: `GET https://scenius-digest.vercel.app/api/links?group={group}`

Workflow:
1. Fetch links from API (with group filter)
2. Fetch each URL to understand content
3. Generate narrative digest
4. Post to group's output_channel
5. Mark links as published via API

Format:
```
🔗 {Group Name} Links Digest
🗓 Week of [Monday date of current week]

[Opening sentence about what the community explored this week.]

📚 Worth Reading / 📰 News / 📚 Resources (topic-appropriate)

[1-2 sentence description per link - why it's interesting, why it matters]

• [Title] - [URL]

🎭 Memes & Delight (if applicable)

[Brief fun intro]

• [URL]
```

### Important Notes

- **No closing CTA**: Do NOT add a closing line inviting people to contribute or join. The output channels are public-facing and read by non-members who can't post to the source group.
- **Week starts on Monday**: The "Week of" date should always be the Monday of the current week.
- **Aware of prior posts**: The API returns only unpublished links, but other links may have already been posted to the channel earlier in the week. Don't comment on volume (e.g., "just one link this week") since there may have been earlier digest posts in the same week.

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

## Telegram Groups

| Group | Key | Group ID | Output Channel | Topics |
|-------|-----|----------|----------------|--------|
| Sensemaking Scenius | scenius | -1002141367711 | -1002708526104 (@scenius) | links, memes |
| Citizen Infra Builders | cibc | -1003188266615 | -1001800461815 (@citizen_infra) | news, resources |
