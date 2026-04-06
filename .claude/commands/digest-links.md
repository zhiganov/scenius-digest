# Generate Weekly Links Digest

Fetch collected links from the bot and publish a digest to the appropriate channel.

## Usage

```
/digest-links [group]
```

- `/digest-links scenius` - Digest for Sensemaking Scenius → @scenius channel
- `/digest-links cibc` - Digest for Citizen Infra Builders → @citizen_infra channel
- `/digest-links` (no arg) - Ask which group to generate for

## Groups

| Group | Output Channel | Chat ID |
|-------|---------------|---------|
| scenius | @scenius | -1002708526104 |
| cibc | @citizen_infra | -1001800461815 |

## Steps

1. Determine which group (from argument or ask user)

2. Fetch links from the bot API:
   ```
   GET https://scenius-digest.vercel.app/api/links?group={group}
   ```

3. For each link, fetch the URL to understand what it's about (use Firecrawl for links where OG metadata is insufficient)

4. Draft the digest following the format below. Use the `message_text` field for context on why links were shared.

5. **Review checkpoint**: Present the draft to the user for approval. Show:
   - The full digest text
   - Character count and whether it fits in one Telegram message (limit: 4096 chars)
   - If over the limit, suggest which links to cut or how to shorten

   Wait for user confirmation. The user may ask to remove links, rewrite sections, or adjust tone. Iterate until approved.

6. Post the approved digest to the group's output channel via Telegram Bot API. Use Node.js (not curl or python) for reliable JSON serialization on Windows:
   ```js
   node -e "
   const text = `PASTE_DIGEST_HERE`;
   fetch('https://api.telegram.org/bot${BOT_TOKEN}/sendMessage', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({chat_id: 'CHAT_ID', text, disable_web_page_preview: true})
   }).then(r => r.json()).then(j => console.log(JSON.stringify(j, null, 2)));
   "
   ```

   BOT_TOKEN: stored as Vercel env var for scenius-digest project. Pull with `npx vercel env pull` from `scenius-digest/`, or read from `scenius-digest/.env.local` if already pulled.

   **Windows note**: Do NOT use `/tmp/` for temp files — Node.js resolves it to `C:\tmp\` which doesn't exist. Use `$HOME/` or inline the text directly in the Node.js script.

7. After posting, mark links as published:
   ```
   POST https://scenius-digest.vercel.app/api/mark-published
   {"ids": [1, 2, 3]}
   ```

## Format

```
🔗 {Group Name} Links Digest
🗓 Week of {Monday date of current week}

[Opening sentence about what the community explored this week.]

📚 Worth Reading (or 📰 News / 📚 Resources depending on topics)

[1-2 sentence description per link - why it's interesting, why it matters]
Include sharer context from message_text when relevant (e.g., "via @username")

• [Title] - [URL]

🎭 Memes & Delight (if applicable)

[Brief fun intro]

• [URL]
```

## Important Notes

- **No closing CTA**: Do NOT add a closing line inviting people to contribute or join. The output channels are public-facing and read by non-members who can't post to the source group.
- **Week starts on Monday**: The "Week of" date should always be the Monday of the current week.
- **Aware of prior posts**: The API returns only unpublished links, but other links may have already been posted to the channel earlier in the week. Don't comment on volume (e.g., "just one link this week") since there may have been earlier digest posts in the same week.

## Writing Style

- Narrative and engaging, not just bullet points
- Highlight interesting/novel ideas
- Specific details (numbers, names, concepts)
- Conversational tone for Telegram
- Credit sharers when relevant
