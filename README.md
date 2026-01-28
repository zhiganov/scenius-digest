# Community Digest Bot

Curated highlights from multiple communities, automatically published to their respective Telegram channels.

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
- Trigger: Manual via `/digest-links [group]` command in Claude Code

## Architecture

```
┌───────────────┐              ┌──────────────────┐
│ Zoom Meetings │              │ Telegram Groups  │
└───────┬───────┘              └────────┬─────────┘
        │                               │
        ▼                               ▼
┌───────────────┐              ┌──────────────────┐
│ Fireflies.ai  │              │ @sensemaking_bot │
│ (transcripts) │              │    (Fly.io)      │
└───────┬───────┘              └────────┬─────────┘
        │                               │
        └───────────┬───────────────────┘
                    ▼
           ┌─────────────────┐
           │   Claude Code   │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │ Output Channels │
           │ (@scenius, etc) │
           └─────────────────┘
```

## Setup

### Meeting Digests
Uses Claude Code with Fireflies MCP:
- Fireflies.ai for meeting transcripts
- Posts via Telegram Bot API
- See [CLAUDE.md](CLAUDE.md) for digest format guidelines

### Links Monitor Bot
Self-hosted Python bot - see [bot/README.md](bot/README.md) for:
- Multi-group configuration
- Local development setup
- Fly.io deployment instructions

## Bot API

Deployed at `https://scenius-digest-bot.fly.dev`:

| Endpoint | Description |
|----------|-------------|
| `GET /api/links` | All unpublished links |
| `GET /api/links?group=cibc` | Links from specific group |
| `GET /api/groups` | List configured groups |

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
- **Bot token** - for posting to Telegram (stored as Fly.io secret)

Contact [@zhiganov](https://t.me/zhiganov) if you want to help with digest generation.

## Adding a New Community

1. Add bot to the Telegram group as admin
2. Run `/debug` in topics to get IDs
3. Edit `bot/groups.json` with the new group config
4. Run `fly deploy` from `bot/` directory

## Contributing

This is an open source project by [Sensemaking Scenius](https://github.com/sensemaking-scenius). PRs welcome!
