# Community Digest Bot

Curated highlights from multiple communities, automatically published to their respective Telegram channels. Also powers the Community Digest feed and Participation (events) in [My Community](https://github.com/Citizen-Infra/my-community) and [Dear Neighbors](https://github.com/Citizen-Infra/dear-neighbors) Chrome extensions via the REST API.

## Supported Communities

| Community | Output Channel |
|-----------|----------------|
| Sensemaking Scenius | [@scenius](https://t.me/scenius) |
| Citizen Infra Builders | [@citizen_infra](https://t.me/citizen_infra) |

## What It Does

### 1. Meeting Digests
Summarizes community Zoom calls and publishes engaging narrative recaps.
- Source: Fireflies.ai transcripts (auto-recorded from Zoom)
- Trigger: Manual via `/digest-meeting` command in Claude Code

### 2. Weekly Links Roundup
Monitors community conversations and curates the best links shared each week.
- Source: Telegram group topics (Links, Memes, News, Resources, etc.)
- Content understanding: [Firecrawl](https://www.firecrawl.dev/) scrapes each link to generate rich descriptions
- Trigger: Manual via `/digest-links [group]` command in Claude Code (autonomous generation planned — see [Roadmap](#roadmap))

### 3. Events Aggregation
Unified events feed from multiple sources, consumed by MC and DN extensions.
- Source A: Telegram event links (enriched with date/location from Luma API, Meetup/Eventbrite ld+json)
- Source B: External event APIs (Luma calendar polling)
- Served via `GET /api/events` with community and city filters

## Architecture

```
┌───────────────┐   ┌──────────────────┐        ┌───────────────┐
│ Zoom Meetings │   │ Telegram Groups  │        │ External APIs │
└───────┬───────┘   └────────┬─────────┘        │ (Luma, etc.)  │
        │                    │                  └───────┬───────┘
        ▼                    ▼                          │
┌───────────────┐   ┌──────────────────┐         ┌──────┴───────┐
│ Fireflies.ai  │   │ Vercel Webhook   │         │   REST API   │
│ (transcripts) │   │ + OG metadata    ├────────►│ GET /api/... │
└───────┬───────┘   │ + event enrich   │         └──────┬───────┘
        │           │ + Supabase       │                │
        │           └────────┬─────────┘                ▼
        │                    │              ┌─────────────────────────────────┐
        │              ┌─────┴─────┐        │ Chrome Extensions               │
        │              │ Firecrawl │        │ (Dear Neighbors, My Community)  │
        │              │ (scraping)│        └─────────────────────────────────┘
        │              └─────┬─────┘
        └────────┬───────────┘
                 ▼
        ┌─────────────────┐
        │   Claude Code   │
        │ (or Claude API) │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ POST /api/      │
        │ send_message    │──────► Telegram Channels
        └─────────────────┘
```

## Setup

### Meeting Digests
Uses Claude Code with Fireflies MCP:
- Fireflies.ai for meeting transcripts
- Posts via Telegram Bot API
- See [CLAUDE.md](CLAUDE.md) for digest format guidelines

### Links Monitor
Serverless Python functions on Vercel with Supabase storage.

```bash
# Deploy
vercel --prod

# Set environment variables
vercel env add BOT_TOKEN
vercel env add WEBHOOK_SECRET
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY

# Register Telegram webhook
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://scenius-digest.vercel.app/api/webhook","secret_token":"...","allowed_updates":["message"]}'
```

## API

Deployed at `https://scenius-digest.vercel.app`. Used by Claude Code for digest generation, by [My Community](https://github.com/Citizen-Infra/my-community) for the digest feed + events, and by [Dear Neighbors](https://github.com/Citizen-Infra/dear-neighbors) for events.

| Endpoint | Description |
|----------|-------------|
| `GET /api/links` | Unpublished links (for digest generation) |
| `GET /api/links?all=true` | All links including published (for My Community) |
| `GET /api/links?group=cibc` | Links from specific group |
| `GET /api/events` | All upcoming events across communities |
| `GET /api/events?community=nsrt` | Events for a specific community |
| `GET /api/events?city=novi-sad` | Events by city (used by Dear Neighbors) |
| `GET /api/groups` | List configured groups with event metadata |
| `POST /api/mark-published` | Mark as published: `{"ids": [1,2,3]}` |
| `POST /api/send_message` | Post to Telegram: `{"chat_id": "...", "text": "..."}` |
| `GET /api/health` | Health check |

## Claude Code Commands

This repo includes custom slash commands for Claude Code:

| Command | Description |
|---------|-------------|
| `/digest-links` | Generate weekly links roundup (asks which group) |
| `/digest-links scenius` | Generate digest for Scenius |
| `/digest-links cibc` | Generate digest for CIBC |
| `/digest-meeting` | Generate digest from latest meeting |

### Usage

```bash
git clone https://github.com/sensemaking-scenius/scenius-digest
cd scenius-digest
claude  # start Claude Code
```

Then type `/digest-links scenius` or `/digest-meeting`.

### Requirements

To use these commands, you need Claude Code configured with:
- **Fireflies MCP** - for accessing meeting transcripts (meeting digests only)
- **Firecrawl MCP** - for scraping link content to generate rich descriptions (links digests)
- **Bot token** - for posting to Telegram (stored as Vercel env var)

Contact [@zhiganov](https://t.me/zhiganov) if you want to help with digest generation.

## Adding a New Community

1. Add bot to the Telegram group as admin
2. Run `/debug` in topics to get IDs
3. Edit `groups.json` with the new group config
4. Deploy: `vercel --prod`
5. No webhook re-registration needed (same endpoint)

## Roadmap

### Autonomous Digest Generation

Currently, digest generation requires a Claude Code session — someone runs `/digest-links scenius`, Claude scrapes the links via Firecrawl, writes the narrative, and posts it. The goal is to make this fully autonomous.

The API surface is almost complete:

| Step | Endpoint | Status |
|------|----------|--------|
| Fetch links | `GET /api/links?group={group}` | Done |
| Scrape & generate narrative | `POST /api/generate-digest` | Planned |
| Post to Telegram | `POST /api/send_message` | Done |
| Mark as published | `POST /api/mark-published` | Done |

The missing piece is a serverless function that calls the Claude API with link metadata (OG titles/descriptions are already stored) to generate the digest narrative. This would enable:
- **Scheduled digests** via Vercel cron or GitHub Actions
- **Bot-triggered digests** via a `/digest` Telegram command
- **Community-run digests** without needing Claude Code access

See [GitHub issue #1](https://github.com/sensemaking-scenius/scenius-digest/issues/1).

### Slack Integration

Multi-platform link collection from Slack workspaces (starting with Metagov). See `docs/plans/2026-02-12-slack-integration-design.md`.

## Contributing

This is an open source project by [Sensemaking Scenius](https://github.com/sensemaking-scenius). PRs welcome!
