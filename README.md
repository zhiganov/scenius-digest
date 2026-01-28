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
│   Claude Code   │     │ @sensemaking_bot│
│ + Fireflies MCP │     │   (Fly.io)      │
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
Uses Claude Code with Fireflies MCP:
- Fireflies.ai for meeting transcripts
- Posts via Telegram Bot API (no Zapier needed)
- See [CLAUDE.md](CLAUDE.md) for digest format guidelines

### Links Monitor Bot
Self-hosted Python bot - see [bot/README.md](bot/README.md) for:
- Local development setup
- Fly.io deployment instructions
- Configuration options

## Telegram

- **Bot:** @sensemaking_bot
- **Channel:** [@scenius](https://t.me/scenius)

## Claude Code Commands

This repo includes custom slash commands for Claude Code:

| Command | Description |
|---------|-------------|
| `/digest-links` | Generate weekly links roundup from collected links |
| `/digest-meeting` | Generate digest from latest Scenius meeting |

### Usage

```bash
git clone https://github.com/sensemaking-scenius/scenius-digest
cd scenius-digest
claude  # start Claude Code
```

Then type `/digest-links` or `/digest-meeting`.

### Requirements

To use these commands, you need Claude Code configured with:
- **Fireflies MCP** - for accessing meeting transcripts (meeting digests only)
- **Bot token** - for posting to Telegram (stored in slash command files)

Contact [@zhiganov](https://t.me/zhiganov) if you want to help with digest generation.

## Contributing

This is an open source project by [Sensemaking Scenius](https://github.com/sensemaking-scenius). PRs welcome!
