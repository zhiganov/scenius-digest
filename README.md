# Community Digest Bot

Curated highlights from multiple communities, automatically published to their respective Telegram channels. Also powers the Community Digest feed and Participation (events) in [My Community](https://github.com/Citizen-Infra/my-community) and [Dear Neighbors](https://github.com/Citizen-Infra/dear-neighbors) Chrome extensions via the REST API.

## Supported Communities

| Community | Output Channel |
|-----------|----------------|
| Sensemaking Scenius | [@scenius](https://t.me/scenius) |
| Citizen Infra Builders | [@citizen_infra](https://t.me/citizen_infra) |
| Novi Sad Relational Tech | [@nsrt_news](https://t.me/nsrt_news) |

## What It Does

### 1. Meeting Digests
Summarizes community Zoom calls and publishes engaging narrative recaps.
- Source: Fireflies.ai transcripts (auto-recorded from Zoom)
- Trigger: Manual via `/digest-meeting` command in Claude Code

### 2. Weekly Links Roundup
Monitors community conversations and curates the best links shared each week.
- Source: Telegram group topics (Links, Memes, News, Resources, etc.)
- Trigger: Manual via `/digest-links [group]` command in Claude Code

### 3. Events Aggregation
Unified events feed from multiple sources, consumed by MC and DN extensions.
- Source A: Telegram event links (enriched with date/location from Luma API, Meetup/Eventbrite ld+json)
- Source B: External event APIs (Luma calendar polling)
- Served via `GET /api/events` with community and city filters

## Architecture

```
┌───────────────┐   ┌──────────────────┐        ┌───────────────┐   ┌───────────────┐
│ Zoom Meetings │   │ Telegram Groups  │        │ External APIs │   │ Admin Panel   │
└───────┬───────┘   └────────┬─────────┘        │ (Luma, etc.)  │   │   (planned)   │
        │                    │                  └───────┬───────┘   └───────────────┘
        ▼                    ▼                          │
┌───────────────┐   ┌──────────────────┐        ┌──────┴───────┐
│ Fireflies.ai  │   │ Vercel Webhook   │        │   REST API   │
│ (transcripts) │   │ + OG metadata    ├───────►│ GET /api/... │
└───────┬───────┘   │ + event enrich   │        └──────┬───────┘
        │           │ + Supabase       │               │
        │           └────────┬─────────┘               ▼
        │                    │          ┌──────────────────────────────────┐
        └────────┬───────────┘          │ Chrome Extensions:               │
                 ▼                      │ Dear Neighbors · My Community    │
        ┌─────────────┐                 └──────────────────────────────────┘
        │ Claude Code │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │  Telegram   │
        │  Channels   │
        └─────────────┘
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
- **Bot token** - for posting to Telegram (stored as Vercel env var)

Contact [@zhiganov](https://t.me/zhiganov) if you want to help with digest generation.

## Adding a New Community

1. Add bot to the Telegram group as admin
2. Run `/debug` in topics to get IDs
3. Edit `groups.json` with the new group config
4. Deploy: `vercel --prod`
5. No webhook re-registration needed (same endpoint)

## Contributing

This is an open source project by [Sensemaking Scenius](https://github.com/sensemaking-scenius). PRs welcome!
