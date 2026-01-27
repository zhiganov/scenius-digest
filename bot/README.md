# Scenius Links Monitor Bot

Monitors a Telegram group for links shared in specific topics and posts weekly digests to @scenius.

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
- `/digest` - Manually trigger digest (for testing)

## Deployment

For 24/7 operation, deploy to:
- **Railway** - Easy Python hosting
- **Fly.io** - Free tier available
- **VPS** - Run with systemd or supervisor

Example systemd service:
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
