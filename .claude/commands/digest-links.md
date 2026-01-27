# Generate Weekly Links Digest

Fetch collected links from the Scenius bot and publish a digest to @scenius.

## Steps

1. Fetch links from the bot API:
   ```
   GET https://scenius-digest-bot.fly.dev/api/links
   ```

2. For each link, fetch the URL to understand what it's about

3. Generate an engaging narrative digest following the format in CLAUDE.md

4. Post the digest to the @scenius Telegram channel (chat_id: -1002708526104)

5. After posting, mark links as published via the API

## Format

See CLAUDE.md for the full format guidelines. Key points:
- Opening line about what the community explored this week
- For each link: 1-2 sentence description of why it's interesting
- Group by topic (Links vs Memes & Delight)
- Conversational, engaging tone
