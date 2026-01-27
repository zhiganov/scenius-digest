# Scenius Digest - Claude Instructions

## Purpose
Generate and publish digests to the public Telegram channel @scenius:
1. **Meeting digests** - Summaries of biweekly Scenius calls
2. **Weekly links roundup** - Curated links shared by the community

---

## 1. Meeting Digests

### Source
Fireflies.ai transcripts. Filter by meetings with **"scenius"** in the title:
```
keyword:"scenius" scope:title
```

### Format
```
📋 [Meeting Title] Digest
🗓 [Date] • ⏱ [Duration] min

[Engaging narrative paragraphs that tell the story of what was discussed. Highlight interesting ideas, projects, and insights. Use a conversational tone that makes readers feel like they were there. Include specific details that make it compelling - numbers, project names, interesting concepts.]

[Second paragraph diving deeper into one or two highlights that would interest people outside the community.]
```

---

## 2. Weekly Links Roundup

### Source
User provides output from `/export` command in the Telegram group bot. This contains links collected from "Links" and "Memes & Delight" topics.

### Workflow
1. User runs `/export` in the Telegram group
2. User shares the output with Claude
3. Claude fetches each link to understand what it's about
4. Claude generates an engaging narrative digest
5. Claude posts to @scenius channel

### Format
```
🔗 Weekly Links Roundup
🗓 Week of [Date]

[Opening sentence about what the community has been exploring this week.]

📚 Worth Reading

[For each interesting link: 1-2 sentence description of why it's interesting, what it's about, and why Scenius folks are sharing it. Make it compelling - don't just describe, explain why it matters.]

• [Title or description] - [URL]

🎭 Memes & Delight

[Brief fun intro for the lighter content]

• [URL]

[Closing line inviting people to join the conversation]
```

### Process for Links
- Fetch each URL to understand its content
- Write engaging descriptions (not just titles)
- Group thematically if there are patterns
- Skip broken links or duplicates
- Credit sharers when it adds context (e.g., "via @username")

---

## Writing Style (Both Types)

- Narrative and engaging, not bullet points
- Highlight the most interesting/novel ideas
- Include specific details (numbers, project names, concepts)
- Make it feel like sharing exciting discoveries with friends
- Conversational tone appropriate for Telegram

## What NOT to Include

- Action items (internal task assignments)
- Internal governance details
- Sensitive or private discussions
- Broken links

## Telegram Channel

- Channel: @scenius (https://t.me/scenius)
- Chat ID: -1002708526104
- Bot: @sensemaking_bot
