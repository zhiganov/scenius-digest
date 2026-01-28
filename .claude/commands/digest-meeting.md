# Generate Meeting Digest

Summarize the latest Scenius meeting and publish to @scenius.

## Steps

1. Search Fireflies for recent Scenius meetings:
   ```
   keyword:"scenius" scope:title
   ```

2. Get the summary from the most recent meeting (or one specified by user)

3. Generate an engaging narrative digest following the format in CLAUDE.md

4. Post the digest to @scenius via Telegram Bot API:
   ```bash
   curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
     -H "Content-Type: application/json" \
     -d '{"chat_id": "-1002708526104", "text": "...", "disable_web_page_preview": true}'
   ```

   BOT_TOKEN: Get via `fly secrets list -a scenius-digest-bot` or ask @zhiganov

## Format

See CLAUDE.md for the full format guidelines. Key points:
- Header with meeting title, date, duration
- Narrative paragraphs telling the story of what was discussed
- Highlight interesting ideas, projects, insights
- No action items or internal assignments
- Conversational tone
