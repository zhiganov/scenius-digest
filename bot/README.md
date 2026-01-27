# Scenius Links Monitor Bot

Monitors a Telegram group for links shared in specific topics. Links are collected automatically, then you ask Claude to generate and post engaging weekly digests to @scenius.

## Setup

### 1. Get Bot Token

You already have @sensemaking_bot. Get its token from @BotFather:
- Message @BotFather
- Send `/mybots` → select @sensemaking_bot → API Token

### 2. Add Bot to Your Group

- Add @sensemaking_bot to your private Telegram group
- Make it admin (so it can read messages)

### 3. Get Group and Topic IDs

In the group, send `/debug` in each topic you want to monitor:
- Go to "Links" topic → send `/debug` → note the Chat ID and Topic/Thread ID
- Go to "Memes & Delight" topic → send `/debug` → note the Topic/Thread ID

### 4. Configure Environment

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

### 5. Install & Run

```bash
cd bot
pip install -r requirements.txt
python bot.py
```

## Commands

- `/debug` - Show chat and topic IDs (for setup)
- `/stats` - Show current week's link counts
- `/export` - Export collected links (share with Claude to generate digest)
- `/digest` - Post basic auto-generated digest (for testing)

## Weekly Workflow

1. Bot runs 24/7, collecting links from monitored topics
2. Each week, run `/export` in the group
3. Copy the output and share with Claude
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

## Schedule

By default, digests post every Monday at 9 AM UTC. Change via environment:
- `DIGEST_DAY` - 0=Monday, 6=Sunday
- `DIGEST_HOUR` - Hour in UTC (0-23)
