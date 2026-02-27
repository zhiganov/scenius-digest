# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-community digest system that collects links from Telegram groups (and soon Slack) and serves them via two channels: curated Telegram digests (via Claude Code) and a REST API consumed by [My Community](https://github.com/Citizen-Infra/my-community) Chrome extension.

**Supported communities:**
- **Sensemaking Scenius** → Telegram → @scenius channel
- **Citizen Infra Builders** → Telegram → [@citizen_infra](https://t.me/citizen_infra) channel
- **Novi Sad Relational Tech (NSRT)** → Telegram → [@nsrt_news](https://t.me/nsrt_news) channel
- **Newspeak House** → events only via `event_sources.json` (Luma, London) — managed by community-admin
- **Civic Tech Toronto** → events only via `event_sources.json` (guild.host) — managed by community-admin
- **Metagov** → events only via `event_sources.json` (Luma) — managed by community-admin

Four outputs:
1. **Meeting digests** — Narrative summaries of Zoom calls (transcripts via Fireflies.ai) → Telegram
2. **Weekly links roundup** — Curated links from community Telegram topics → Telegram
3. **REST API — Links** — Links with OG metadata served to My Community extension (`GET /api/links`, `/api/groups`)
4. **REST API — Events** — Unified events feed aggregating Telegram event links + external APIs (Luma), served to My Community and Dear Neighbors extensions (`GET /api/events`)

## Architecture

```
Zoom Meetings ──► Fireflies.ai ──┐
                                 ├──► Claude Code ──► Telegram Channels
Telegram Groups ──► Webhook ──► Supabase
                   (+ OG/events)    ├──► /api/links ──► My Community (digest feed)
Slack Workspaces ─► Slack Event ──┘ ├──► /api/events ──► MC + DN (participation)
                   (planned)        │
External APIs ──────────────────────┘    (Luma, guild.host)
```

**Serverless functions** (`api/`):
- `api/webhook.py` - Telegram webhook handler (receives messages, fetches OG metadata, enriches events, stores links)
- `api/links.py` - GET links (used by Claude Code for digests and My Community for the digest feed)
- `api/events.py` - GET unified events feed (aggregates Telegram event links + external APIs like Luma). Filters: `?community=nsrt`, `?city=novi-sad`
- `api/groups.py` - GET configured groups with city/event metadata (used by MC for community selection)
- `api/mark_published.py` - POST mark links as published
- `api/backfill_og.py` - POST backfill OG metadata for existing links missing it
- `api/health.py` - GET health check

**Shared modules** (`lib/`):
- `lib/config.py` - Env vars + groups.json/event_sources.json loading + helpers (`is_event_topic()`, `get_all_event_groups()`)
- `lib/database.py` - Supabase client (`digest_links` table, `add_link()`, `get_event_links()`)
- `lib/telegram.py` - Telegram Bot API helper (sendMessage via urllib)
- `lib/opengraph.py` - Open Graph metadata fetcher (stdlib only, 5s timeout, 32KB read limit)
- `lib/event_enrichment.py` - Event platform detection (Luma/Meetup/Eventbrite) + structured data extraction
- `lib/luma.py` - Luma calendar API fetcher (future events from a calendar URL)
- `lib/guildhost.py` - guild.host events fetcher (scrapes Relay store from SSR page via bot user-agent)
- `lib/eventus.py` - eventus.city events fetcher (archived — events lacked metadata and linked to unrelated Telegram groups)

**Design docs** (`docs/plans/`):
- `2026-02-08-events-aggregation-design.md` - Events API design (implemented)
- `2026-02-12-slack-integration-design.md` - Slack bot integration for multi-platform link digests

**Slash commands** (`.claude/commands/`):
- `digest-links.md` - Weekly links roundup workflow (supports group argument)
- `digest-meeting.md` - Meeting digest workflow

**Legacy** (`bot/`): Original Fly.io bot (python-telegram-bot + SQLite + aiohttp). Kept for reference only — not deployed.

## Multi-Group Configuration

Telegram-based communities are defined in `groups.json` (project root). Non-Telegram communities with external event sources only are in `event_sources.json` (interim — will be replaced by community-admin's `GET /api/config`).

```json
{
  "scenius": {
    "name": "Sensemaking Scenius",
    "group_id": "-1002141367711",
    "output_channel": "-1002708526104",
    "city": null,
    "topics": { "links": "230", "memes": "4605", "events": "2156", "ai-tools-library": "6430" },
    "event_topics": ["events"],
    "event_apis": []
  },
  "nsrt": {
    "name": "Novi Sad Relational Tech",
    "group_id": "-1003669626939",
    "output_channel": "-1003857482838",
    "city": "novi-sad",
    "topics": { "links": "16", "events": "8" },
    "event_topics": ["events"],
    "event_apis": [{ "type": "luma", "url": "https://luma.com/cibc", "api_id": "cal-8H09wJN7syCCaRR" }]
  }
}
```

Each group in `groups.json` can have:
- `platform` — `"telegram"` (default if omitted) or `"slack"`. Determines ingestion path.
- `city` — slug for `/api/events?city=` filtering (used by Dear Neighbors)
- `event_topics` — Telegram topics where links are treated as events (enriched with date/location)
- `event_apis` — external event sources polled by `/api/events` (Luma calendars, guild.host communities)

Each entry in `event_sources.json` has: `name`, `city`, and `event_apis`. The events API (`/api/events`) merges both files when querying.
  - Luma: `{ "type": "luma", "url": "...", "api_id": "cal-..." }` — `api_id` is required since Luma migrated from lu.ma to luma.com and the URL slug no longer works as an API key. Find the `cal-` ID by searching for `cal-` in the page source of the Luma calendar page.
  - guild.host: `{ "type": "guildhost", "url": "https://guild.host/{slug}/events" }` — scrapes SSR page using bot user-agent

### Slack Integration (planned)

Slack-based communities (like Metagov) use an OAuth-installed Slack app instead of the Telegram webhook. Channel-to-topic mappings are stored in a `slack_installations` Supabase table, not in `groups.json`. Links are stored in the same `digest_links` table with `source = 'slack'`. Digests still post to Telegram. See `docs/plans/2026-02-12-slack-integration-design.md` for full design.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (see .env.example)
cp .env.example .env

# Deploy to Vercel (manual — GitHub auto-deploy broken, needs org owner to authorize Vercel GitHub App for sensemaking-scenius org)
npx vercel --prod --scope team_gEI6i7fAEHyXy1j3KYQIFpPw

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

## API

Deployed at `https://scenius-digest.vercel.app`. Consumed by Claude Code (digest generation) and My Community extension (digest feed).

| Endpoint | Description |
|----------|-------------|
| `GET /api/links` | All unpublished links |
| `GET /api/links?group=cibc` | Links from specific group |
| `GET /api/links?days=14` | Links from last N days |
| `GET /api/links?all=true` | All links including published (for MC digest feed) |
| `GET /api/events` | All upcoming events across communities |
| `GET /api/events?community=nsrt` | Events for a specific community |
| `GET /api/events?city=novi-sad` | Events for communities in a city (used by DN) |
| `GET /api/groups` | List configured groups with city/event metadata |
| `POST /api/mark-published` | Mark as published: `{"ids": [1,2,3]}` |
| `GET /api/health` | Health check |

Links response includes `group_id`, `group_name`, `message_text`, and OG metadata fields (`og_title`, `og_description`, `og_image`) when available.

Events response includes `id`, `title`, `description`, `image`, `url`, `starts_at`, `ends_at`, `location`, `source` (telegram/luma/guildhost), and `community`.

## Bot Commands

Send these in a monitored Telegram group:

| Command | Description |
|---------|-------------|
| `/debug` | Show chat/topic IDs, check if monitored |
| `/groups` | List all configured groups |
| `/stats [group]` | Show link statistics |

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
  published BOOLEAN DEFAULT FALSE,
  og_title TEXT,
  og_description TEXT,
  og_image TEXT,
  type TEXT DEFAULT 'link',          -- 'link' or 'event'
  event_starts_at TIMESTAMPTZ,       -- event start time (enriched)
  event_location TEXT                 -- event location (enriched)
);
```

OG metadata (`og_title`, `og_description`, `og_image`) is fetched automatically when the webhook stores a new link. Uses stdlib `urllib` with a 5-second timeout and reads only the first 32KB of HTML. Falls back to `<title>` and `<meta name="description">` when OG tags are absent. Consumers should prefer `og_title` over `title` and `og_description` over `description` when available.

**Event enrichment:** Links shared in `event_topics` are stored with `type='event'`. The webhook calls `enrich_event()` which extracts structured data (start time, location) from known platforms — Luma (both `lu.ma` and `luma.com` domains) via public API, Meetup/Eventbrite via ld+json parsing. The `/api/events` endpoint also re-enriches Telegram events at read time to pick up rescheduled dates and updated locations.

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

## Communities

| Community | Key | Config file | Link source | Digest output | Events |
|-----------|-----|-------------|-------------|---------------|--------|
| Sensemaking Scenius | scenius | groups.json | TG topics: links, memes, events, ai-tools-library | @scenius | TG events |
| Citizen Infra Builders | cibc | groups.json | TG topics: news, resources, events | @citizen_infra | TG events + Luma |
| Novi Sad Relational Tech | nsrt | groups.json | TG topics: links, events | @nsrt_news | TG events + Luma |
| Newspeak House | newspeak-house | event_sources.json | — (community-admin) | — | Luma |
| Civic Tech Toronto | civic-tech-toronto | event_sources.json | — (community-admin) | — | guild.host |
| Metagov | metagov | event_sources.json | — (community-admin) | — | Luma |
