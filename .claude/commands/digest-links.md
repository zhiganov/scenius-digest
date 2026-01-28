# Generate Weekly Links Digest

Fetch collected links from the Scenius bot and publish a digest to @scenius.

## Steps

1. Fetch links from the bot API:
   ```
   GET https://scenius-digest-bot.fly.dev/api/links
   ```

2. For each link, fetch the URL to understand what it's about (use Firecrawl)

3. Generate an engaging narrative digest following the format in CLAUDE.md. Use the `message_text` field for context on why links were shared.

4. Post the digest to @scenius via Telegram Bot API:
   ```bash
   curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
     -H "Content-Type: application/json" \
     -d '{"chat_id": "-1002708526104", "text": "...", "disable_web_page_preview": true}'
   ```

   BOT_TOKEN: `8511113052:AAEPY6UeziC7FoniUibvIduBlDA8rBb77og`

5. After posting, mark links as published:
   ```
   POST https://scenius-digest-bot.fly.dev/api/mark-published
   {"ids": [1, 2, 3]}
   ```

## Format

See CLAUDE.md for the full format guidelines. Key points:
- Opening line about what the community explored this week
- For each link: 1-2 sentence description of why it's interesting
- Include sharer context from message_text when relevant
- Group by topic (Links vs Memes & Delight)
- Conversational, engaging tone
