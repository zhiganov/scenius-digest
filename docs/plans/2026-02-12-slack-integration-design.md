# Slack Integration for Multi-Platform Link Digests

*2026-02-12*

## Context

scenius-digest currently collects links exclusively from Telegram groups. We want to add Metagov as a community — they use Slack, not Telegram. Their Luma calendar events can be added immediately (same as Newspeak House / Civic Tech Toronto), but link collection requires a new ingestion path from Slack.

This design adds a parallel Slack ingestion pipeline alongside the existing Telegram webhook. Everything downstream — storage, API, digest generation, and Telegram distribution — stays unchanged.

## Design Decisions

- **Slack Events API** for real-time link collection — mirrors the Telegram webhook pattern. Slack pushes `message` events to a Vercel endpoint as they happen.
- **Distributable OAuth app** — Metagov (or any future Slack workspace) installs the app via "Add to Slack" flow. This scales to additional Slack communities without code changes.
- **Cherry-pick channels** — Admin selects a handful of high-signal channels to monitor, each mapped to a topic label (e.g. `"links"`, `"governance"`). Not all channels are monitored.
- **Slack in, Telegram out** — Links are collected from Slack, but the weekly digest is posted to a Telegram channel. Keeps the distribution side completely unchanged.
- **Minimal DB changes** — One new column (`source`) on `digest_links`, one new table (`slack_installations`).

## Architecture

```
Telegram Groups ──→ POST /api/webhook ──────┐
                                             ├──→ digest_links (Supabase)
Slack Workspaces ──→ POST /api/slack-event ──┘         │
                                                       ├──→ GET /api/links
                                                       ├──→ GET /api/events
                                                       └──→ digest → Telegram channel
```

New endpoints:
- `POST /api/slack-event` — receives Slack Events API payloads
- `GET /api/slack-install` — redirects to Slack OAuth with community key in state
- `GET /api/slack-oauth` — OAuth callback, exchanges code for bot token

## Slack App Configuration

**OAuth scopes (bot):**
- `channels:history` — read messages in public channels the bot is in
- `channels:read` — list channels for config
- `users:read` — resolve user IDs to display names

**Event subscriptions:**
- `message.channels` — messages posted in public channels

**Install flow:**

1. Admin visits `/api/slack-install?community=metagov`
2. Redirects to Slack OAuth consent page with `state=metagov`
3. User authorizes in their Slack workspace
4. Slack redirects to `/api/slack-oauth` with auth code
5. Server exchanges code for bot token via `oauth.v2.access`
6. Stores installation in `slack_installations` table
7. Admin invites bot to specific channels via `/invite @scenius-digest` in Slack
8. Admin configures channel-to-topic mapping in the DB

## Database Changes

### New table: `slack_installations`

```sql
CREATE TABLE slack_installations (
  id SERIAL PRIMARY KEY,
  community_key TEXT NOT NULL UNIQUE,
  team_id TEXT NOT NULL,
  team_name TEXT,
  bot_token TEXT NOT NULL,
  channels JSONB DEFAULT '{}',
  installed_at TIMESTAMPTZ DEFAULT NOW()
);
```

The `channels` field maps topic labels to Slack channel IDs:
```json
{
  "links": "C0123ABCDEF",
  "governance": "C0456GHIJKL",
  "events": "C0789MNOPQR"
}
```

Configured manually after install (direct DB update or admin endpoint).

### Existing table: `digest_links`

One new column:
```sql
ALTER TABLE digest_links ADD COLUMN source TEXT NOT NULL DEFAULT 'telegram';
```

Default `'telegram'` — all existing rows are correctly labeled without backfill. New Slack links get `source = 'slack'`.

All other columns map naturally:
- `group_id` → community key (`"metagov"`)
- `group_name` → workspace/community name (`"Metagov"`)
- `topic` → channel label from `slack_installations.channels`
- `shared_by` → resolved Slack display name
- `message_id` → Slack message `ts` (cast to text — e.g. `"1710284672.000100"`)
- `message_text` → full message text
- OG and event fields — identical to Telegram path

## Slack Event Handler

`api/slack-event.py` — mirrors `api/webhook.py`:

1. **URL verification** — Slack sends a one-time challenge on subscription setup. Return `{"challenge": body["challenge"]}`.
2. **Signature verification** — Validate `X-Slack-Signature` header using `SLACK_SIGNING_SECRET`.
3. **Filter events** — Only process `event.type == "message"` without `subtype` (skip edits, joins, bot messages).
4. **Lookup installation** — Find `slack_installations` row by `body.team_id`.
5. **Check channel** — Reverse-lookup `event.channel` in `installation.channels` to get topic. Skip if not monitored.
6. **Extract URLs** — Same regex as Telegram webhook.
7. **Resolve username** — Call `users.info` with the bot token to get display name from `event.user` (Slack user ID). Cache in-memory since the same users post repeatedly.
8. **Process links** — For each URL: fetch OG metadata, enrich events if applicable, store in `digest_links` with `source = 'slack'`.

Duplicate check unchanged: same URL in same `group_id` within 7 days.

## Groups Configuration

New entry in `groups.json`:

```json
"metagov": {
  "name": "Metagov",
  "platform": "slack",
  "group_id": null,
  "output_channel": "-100XXXXXXXXX",
  "topics": [],
  "city": null,
  "event_topics": [],
  "event_apis": [
    {
      "type": "luma",
      "url": "https://luma.com/metagov-calendar",
      "api_id": "cal-XXXXXXXXXX"
    }
  ]
}
```

Key fields:
- `platform: "slack"` — new field. Existing communities default to `"telegram"` if omitted.
- `group_id: null` — no Telegram group (collection is via Slack).
- `output_channel` — Telegram channel ID for digest output (new channel created for Metagov digests).
- `topics: []` — empty. Monitored channels configured in `slack_installations.channels`, not here.
- `event_apis` — Luma calendar, identical pattern to other events-only communities.

`lib/config.py` changes minimally. `get_group_by_chat_id()` stays Telegram-only. Slack lookups go through `slack_installations`. API endpoints (`/api/links`, `/api/events`, `/api/groups`) need no changes — they query `digest_links` by `group_id` which is `"metagov"` regardless of source.

## Environment Variables

New Vercel env vars:
- `SLACK_CLIENT_ID` — from Slack app settings
- `SLACK_CLIENT_SECRET` — from Slack app settings
- `SLACK_SIGNING_SECRET` — for verifying event payloads

## Implementation Sequence

### Phase 1: Metagov events (immediate, no Slack needed)
1. Look up Luma `api_id` for `https://luma.com/metagov-calendar`
2. Add `metagov` entry to `groups.json` with `event_apis` only (events-only community, like Newspeak House)
3. Deploy — Metagov events appear in My Community participation feed

### Phase 2: Database & config prep
4. Add `source` column to `digest_links`
5. Create `slack_installations` table
6. Add `platform` field to `groups.json` config schema

### Phase 3: Slack OAuth
7. Create Slack app at api.slack.com/apps (scopes, event subscriptions, redirect URL)
8. Implement `/api/slack-install` (redirect to Slack OAuth)
9. Implement `/api/slack-oauth` (exchange code, store in `slack_installations`)
10. Add Vercel env vars (`SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_SIGNING_SECRET`)

### Phase 4: Slack event handler
11. Implement `/api/slack-event` (URL verification + message processing)
12. Add Slack username resolution with caching
13. Install app to Metagov workspace, invite bot to chosen channels
14. Configure channel-to-topic mapping in `slack_installations.channels`
15. Update `groups.json` Metagov entry with `output_channel` (new Telegram channel)

### Phase 5: Verify end-to-end
16. Post a test link in a monitored Metagov Slack channel
17. Verify it appears in `digest_links` with `source = 'slack'`
18. Verify it appears in `GET /api/links?group=metagov`
19. Verify My Community shows it in the digest feed
20. Test digest generation for Metagov (posts to Telegram channel)
