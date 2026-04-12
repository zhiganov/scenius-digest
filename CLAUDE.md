# CLAUDE.md

Multi-community digest system: collects links from Telegram groups, serves curated digests and a REST API for the My Community extension.

**Communities:** Scenius (@scenius), CIBC (@citizen_infra), NSRT (@nsrt_news). Plus event-only communities (Newspeak House, Civic Tech Toronto, Metagov) via `event_sources.json`.

**Outputs:** Meeting digests → Telegram, Weekly links roundup → Telegram, REST API for links + events → My Community / Dear Neighbors extensions.

## Commands

```bash
pip install -r requirements.txt
cp .env.example .env

# Deploy (manual — GitHub auto-deploy broken, needs org owner authorization)
npx vercel --prod --scope team_gEI6i7fAEHyXy1j3KYQIFpPw

# Env vars
vercel env add BOT_TOKEN
vercel env add WEBHOOK_SECRET    # dual-use: Telegram webhook secret + Bearer auth for send-message/backfill endpoints
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY
```

### Webhook Registration

```bash
curl "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook"

curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://scenius-digest.vercel.app/api/webhook","secret_token":"YOUR_SECRET","allowed_updates":["message"]}'
```

## API

Deployed at `https://scenius-digest.vercel.app`.

| Endpoint | Description |
|----------|-------------|
| `GET /api/links` | All unpublished links |
| `GET /api/links?group=cibc` | Links from specific group |
| `GET /api/links?days=14` | Links from last N days |
| `GET /api/links?all=true` | All links including published (for MC digest feed) |
| `GET /api/events` | All upcoming events across communities |
| `GET /api/events?community=nsrt` | Events for a specific community |
| `GET /api/events?city=novi-sad` | Events for communities in a city (used by DN) |
| `GET /api/groups` | List configured groups with city/event metadata |
| `POST /api/mark-published` | Mark as published: `{"ids": [1,2,3]}` |
| `POST /api/send-message` | Send message: `{"chat_id": "...", "text": "..."}` (Bearer WEBHOOK_SECRET) |
| `POST /api/backfill-og` | Backfill OG metadata (Bearer WEBHOOK_SECRET) |
| `GET /api/health` | Health check |

Links response includes `group_id`, `group_name`, `message_text`, and OG metadata (`og_title`, `og_description`, `og_image`).

Events response includes `id`, `title`, `description`, `image`, `url`, `starts_at`, `ends_at`, `location`, `source`, `community`.

## Bot Commands

| Command | Description |
|---------|-------------|
| `/debug` | Show chat/topic IDs, check if monitored |
| `/groups` | List all configured groups |
| `/stats [group]` | Show link statistics |

## MCP Integrations

- **Fireflies MCP** — meeting transcripts (`keyword:"scenius" scope:title`)
- **Firecrawl MCP** — scrape link content for digest summaries

## Posting to Telegram

```bash
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "{output_channel}", "text": "...", "disable_web_page_preview": true}'
```

BOT_TOKEN is stored as a Vercel environment variable.

---

## Digest Generation Instructions

### Meeting Digests

Source: Fireflies.ai transcripts filtered by `keyword:"scenius" scope:title`

Format:
```
📋 [Meeting Title] Digest
🗓 [Date] • ⏱ [Duration] min

[Engaging narrative paragraphs - tell the story of what was discussed. Highlight interesting ideas, projects, insights. Conversational tone. Include specific details - numbers, project names, concepts.]

[Second paragraph diving into highlights that would interest people outside the community.]
```

### Weekly Links Roundup

Source: `GET https://scenius-digest.vercel.app/api/links?group={group}`

Workflow:
1. Fetch links from API (with group filter)
2. Fetch each URL to understand content
3. Generate narrative digest
4. Post to group's output_channel
5. Mark links as published via API

Format:
```
🔗 {Group Name} Links Digest
🗓 Week of [Monday date of current week]

[Opening sentence about what the community explored this week.]

📚 Worth Reading / 📰 News / 📚 Resources (topic-appropriate)

[1-2 sentence description per link - why it's interesting, why it matters]

• [Title] - [URL]

🎭 Memes & Delight (if applicable)

[Brief fun intro]

• [URL]
```

### Important Notes

- **No closing CTA**: Do NOT add a closing line inviting people to contribute or join. The output channels are public-facing and read by non-members who can't post to the source group.
- **Week starts on Monday**: The "Week of" date should always be the Monday of the current week.
- **Aware of prior posts**: The API returns only unpublished links, but other links may have already been posted earlier in the week. Don't comment on volume.

### Writing Style

- Narrative and engaging, not bullet points
- Highlight interesting/novel ideas
- Specific details (numbers, names, concepts)
- Conversational tone for Telegram
- Credit sharers when relevant (e.g., "via @username")

### What NOT to Include

- Action items or internal task assignments
- Internal governance details
- Sensitive/private discussions
- Broken links
- Transcript links (require login)

## Communities

| Community | Key | Link source | Digest output | Events |
|-----------|-----|-------------|---------------|--------|
| Sensemaking Scenius | scenius | TG topics: links, memes, events, ai-tools-library | @scenius | TG events |
| Citizen Infra Builders | cibc | TG topics: news, resources, events | @citizen_infra | TG events + Luma |
| Novi Sad Relational Tech | nsrt | TG topics: links, events | @nsrt_news | TG events + Luma |
| Newspeak House | newspeak-house | — (community-admin) | — | Luma |
| Civic Tech Toronto | civic-tech-toronto | — (community-admin) | — | guild.host |
| Metagov | metagov | — (community-admin) | — | Luma |

## Reference

Read when working on internals: [Architecture](docs/architecture.md) — system diagram, serverless functions, shared modules, multi-group config, database schema, event enrichment.
