# Scenius Digest

Curated highlights from the Sensemaking Scenius community, automatically published to [@scenius](https://t.me/scenius).

## What It Does

### 1. Meeting Digests
Summarizes biweekly Scenius meetings and publishes engaging narrative recaps.
- Source: Fireflies.ai transcripts
- Filter: Meetings with "scenius" in the title
- Includes: Town Halls, Panel Discussions, Gem Sharing, Fundraising calls

### 2. Weekly Links Roundup
Monitors community conversations and curates the best links shared each week.
- Source: Telegram group topics ("Links" and "Memes & Delight")
- Schedule: Auto-posts every Monday 9 AM UTC

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Fireflies.ai   │     │ Telegram Group  │
│   (meetings)    │     │ (links/memes)   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   Claude Code   │     │  Monitor Bot    │
│  + Zapier MCP   │     │   (Fly.io)      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
            ┌─────────────────┐
            │ @scenius channel│
            │   (Telegram)    │
            └─────────────────┘
```

## Setup

### Meeting Digests
Uses Claude Code with Zapier MCP integration:
- Fireflies.ai for meeting transcripts
- Zapier MCP for Telegram posting
- See [CLAUDE.md](CLAUDE.md) for digest format guidelines

### Links Monitor Bot
Self-hosted Python bot - see [bot/README.md](bot/README.md) for:
- Local development setup
- Fly.io deployment instructions
- Configuration options

## Telegram

- **Bot:** @sensemaking_bot
- **Channel:** [@scenius](https://t.me/scenius)

## Contributing

This is an open source project by [Sensemaking Scenius](https://github.com/sensemaking-scenius). PRs welcome!
