# Scenius Links Monitor Bot

Monitors a Telegram group for links shared in specific topics. Links are collected automatically, then you ask Claude to generate and post engaging weekly digests to @scenius.

## Setup

### 1. Get Bot Token

You already have @sensemaking_bot. Get its token from @BotFather:
- Message @BotFather
- Send `/mybots` → select @sensemaking_bot → API Token

### 2. Register Commands with BotFather

Message @BotFather to make commands visible in Telegram:
- Send `/mybots` → select your bot → Edit Bot → Edit Commands
- Send:
```
debug - Show chat and topic IDs
stats - Show current week's link counts
digest - Post digest (testing)
```

### 3. Add Bot to Your Group

- Add @sensemaking_bot to your private Telegram group
- Make it admin (so it can read messages)

### 4. Get Group and Topic IDs

In the group, send `/debug` in each topic you want to monitor:
- Go to "Links" topic → send `/debug` → note the Chat ID and Topic/Thread ID
- Go to "Memes & Delight" topic → send `/debug` → note the Topic/Thread ID

### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your values:
```
BOT_TOKEN=123456:ABC-your-token
MONITOR_GROUP_ID=-1001234567890
TOPIC_LINKS_ID=123
TOPIC_MEMES_ID=456
```

### 6. Install & Run

```bash
cd bot
pip install -r requirements.txt
python bot.py
```

## Commands

- `/debug` - Show chat and topic IDs (for setup)
- `/stats` - Show current week's link counts
- `/digest` - Post basic auto-generated digest (for testing)

## API Endpoints

The bot exposes an HTTP API for Claude to fetch links:

- `GET /api/links` - Returns collected links as JSON
- `GET /api/links?days=14` - Links from last 14 days
- `POST /api/mark-published` - Mark links as published (body: `{"ids": [1,2,3]}`)
- `GET /health` - Health check

## Weekly Workflow

1. Bot runs 24/7 on Fly.io, collecting links from monitored topics
2. Ask Claude to "generate links digest"
3. Claude fetches links from `https://scenius-digest-bot.fly.dev/api/links`
4. Claude generates an engaging narrative digest and posts to @scenius

## Deployment (Fly.io)

### 1. Install Fly CLI

```bash
# macOS
brew install flyctl

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Linux
curl -L https://fly.io/install.sh | sh
```

### 2. Login & Launch

```bash
cd bot
fly auth login
fly launch --no-deploy
```

When prompted:
- App name: `scenius-digest-bot` (or your choice)
- Region: pick one close to you
- Don't set up Postgres/Redis

### 3. Create Volume for Database

```bash
fly volumes create scenius_data --size 1 --region ams
```

### 4. Set Secrets

```bash
fly secrets set BOT_TOKEN="your_bot_token_here"
fly secrets set MONITOR_GROUP_ID="-1001234567890"
fly secrets set TOPIC_LINKS_ID="123"
fly secrets set TOPIC_MEMES_ID="456"
```

### 5. Deploy

```bash
fly deploy
```

### 6. Check Logs

```bash
fly logs
```

### Updating

After code changes:
```bash
fly deploy
```

## Alternative: VPS with systemd

```ini
[Unit]
Description=Scenius Links Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/scenius-digest/bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Auto-Post (Optional)

The bot can auto-post basic digests, but Claude Code generates better narrative digests. Auto-post is **disabled by default**.

To enable auto-post (basic formatting only):
```bash
fly secrets set AUTO_POST_ENABLED=true
```

Configure schedule via environment:
- `DIGEST_DAY` - 0=Monday, 6=Sunday (default: 0)
- `DIGEST_HOUR` - Hour in UTC, 0-23 (default: 9)

**Recommended workflow:** Keep auto-post disabled. Use `/digest-links` in Claude Code for narrative digests.
