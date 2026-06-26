# Process Notes — scenius-digest

> **Canonical location:** `claude-config/docs/scenius-digest/process-notes.md` — the private cross-machine config repo. Operational details (env-var rotations, infra decisions, repo-transfer history) live there so they sync across machines and stay out of this public repo's working tree.
>
> Pull the latest claude-config (`zhiganov/claude-config`, private) on each machine. See `claude-config/README.md` for setup.

## 2026-06-22 — Persist message_thread_id (topic-attribution audit)
- **Done:** Closed the topic-attribution observability gap — added `digest_links.topic_thread_id` (Supabase migration + PostgREST reload), threaded it through `add_link` + `webhook.py`, plus a log line when a link is dropped from an unmapped/General topic. Pushed (7e5ad17); closes #11.
- **Decisions:** Round-trip-verified the column. Corrected my own mis-diagnosis that Vercel auto-deploy was broken — #3 was stale (deploys land on push), closed it. The Vercel MCP/CLI token can't see this project (it sits under the "Artem's projects" team, not Harmonica).
- **State:** Merged to main, auto-deploys. `topic_thread_id` populates on the next link in a monitored cibc topic (none since deploy yet).
- **Next:** confirm it populates once a real link lands.

## 2026-06-26 — /api/events: filter to real events + date parsing (#12)
- **Done:** `/api/events` now drops bare-link junk from the Telegram events topic (keep only if dated or an event-page URL) and dates more events: Eventbrite all TLDs, ld+json Event subtypes + `@graph`, generic ld+json fallback for event-ish URLs. Pushed (bd81ad2), deployed, verified live (cibc 16→12, dated 5→7). Closes #12.
- **Decisions:** Enrichment runs live at request time, so the fix took effect on next request. addevent / Zoom-registration pages have no structured data → stay undated (the my-community consumer hides undated). Surfaced during my-community Participation verification.
- **State:** Merged to main, deployed, verified.
- **Next:** none.
