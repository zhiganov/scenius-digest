# Multi-Community Links Monitor Bot

Monitors multiple Telegram groups for links shared in specific topics. Links are collected automatically, then you ask Claude to generate and post engaging weekly digests to each community's channel.

## Supported Communities

| Community | Group Key | Output Channel |
|-----------|-----------|----------------|
| Sensemaking Scenius | `scenius` | @scenius |
| Citizen Infra Builders | `cibc` | [@citizen_infra](https://t.me/citizen_infra) |

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
stats - Show link counts by group
digest - Post digest for a group
groups - List monitored groups
```

### 3. Add Bot to Your Groups

- Add @sensemaking_bot to each Telegram group you want to monitor
- Make it admin (so it can read messages)

### 4. Get Group and Topic IDs

In each group, send `/debug` in the topics you want to monitor:
- Note the Chat ID (group ID)
- Note the Topic/Thread ID for each topic

### 5. Configure Groups

Edit `groups.json` with your groups:

```json
{
  "scenius": {
    "name": "Sensemaking Scenius",
    "group_id": "-1002141367711",
    "output_channel": "-1002708526104",
    "topics": {
      "links": "230",
      "memes": "4605"
    }
  },
  "cibc": {
    "name": "Citizen Infra Builders",
    "group_id": "-1003188266615",
    "output_channel": "-1001800461815",
    "topics": {
      "news": "11",
      "resources": "266"
    }
  }
}
```

### 6. Install & Run Locally

```bash
cd bot
pip install -r requirements.txt
cp .env.example .env  # Add BOT_TOKEN
python bot.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/debug` | Show chat and topic IDs (for setup) |
| `/groups` | List all monitored groups |
| `/stats` | Show link counts for all groups |
| `/stats cibc` | Show link counts for specific group |
| `/digest cibc` | Post digest for specific group |

## API Endpoints

The bot exposes an HTTP API at `https://scenius-digest-bot.fly.dev`:

| Endpoint | Description |
|----------|-------------|
| `GET /api/links` | All unpublished links |
| `GET /api/links?group=cibc` | Links from specific group |
| `GET /api/links?days=14` | Links from last 14 days |
| `GET /api/groups` | List configured groups |
| `POST /api/mark-published` | Mark as published: `{"ids": [1,2,3]}` |
| `GET /health` | Health check |

## Weekly Workflow

1. Bot runs 24/7 on Fly.io, collecting links from all monitored groups
2. Ask Claude: `/digest-links scenius` or `/digest-links cibc`
3. Claude fetches links, generates narrative digest, posts to output channel
4. Links are marked as published

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
- App name: `scenius-digest-bot`
- Region: pick one close to you
- Don't set up Postgres/Redis

### 3. Create Volume for Database

```bash
fly volumes create scenius_data --size 1 --region ams
```

### 4. Set Secrets

```bash
fly secrets set BOT_TOKEN="your_bot_token_here"
```

Note: Group configuration is now in `groups.json`, not environment variables.

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

## Adding a New Group

1. Add bot to the new Telegram group as admin
2. Run `/debug` in each topic to get IDs
3. Add group to `groups.json`
4. Run `fly deploy`

## Auto-Post (Optional)

The bot can auto-post basic digests, but Claude Code generates better narrative digests. Auto-post is **disabled by default**.

To enable auto-post for all groups:
```bash
fly secrets set AUTO_POST_ENABLED=true
```

Configure schedule via environment:
- `DIGEST_DAY` - 0=Monday, 6=Sunday (default: 0)
- `DIGEST_HOUR` - Hour in UTC, 0-23 (default: 9)

**Recommended:** Keep auto-post disabled. Use `/digest-links [group]` in Claude Code for narrative digests.
