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

## 2026-06-27 — #13 gate; community-admin config seam; V7 visibility filter
- **Done:** (1) **#13** — `/api/groups` hides `group_id`/`output_channel` behind a read-only Bearer secret (avails sends it via its own secret); closed. (2) **Config seam** — `config.py` now reads community config from community-admin `GET /api/config` (60s TTL cache; `MONITORED_GROUPS` via PEP-562; `groups.json` fallback); verified live propagation (~60s). (3) **V7** — `/api/groups` / `/api/events` / `/api/links` filter private communities by `?identity=` (members from `/api/config`); verified hidden-from-anon / visible-to-member live.
- **Decisions:** `groups.json` stays as the fallback (zero-disruption; R8 held — consumers unchanged). `?identity=` is self-asserted (obscurity, not access control) → being replaced by verified JWTs (community-admin#21).
- **State:** All deployed + verified live.
- **Next:** IdP **S2** — verify community-admin JWTs via JWKS, filter by the `memberships` claim, drop `?identity=` + `members`-in-`/api/config`.

## 2026-06-27 — IdP S2: verify tokens, drop ?identity=
- **Done:** scenius-digest now verifies community-admin ES256 JWTs offline via JWKS (`lib/auth.py`, PyJWT[crypto]) and gates private communities by the verified `memberships` claim across `/api/groups`, `/api/events`, `/api/links`. Removed the self-asserted `?identity=` param. Added the repo's first pytest suite (11 tests: 6 auth + 5 config). Pushed + deployed.
- **Decisions:** Verify path fails closed — any missing/invalid/expired token or JWKS failure → empty member set → public only; private is never served without a valid token. `CONFIG_READ_SECRET` (#13 avails gate) left untouched; it coexists with the JWT path on `/api/groups`. Built subagent-driven (TDD); Opus final whole-branch review = READY TO ROLL OUT, 0 Critical/Important.
- **State:** Live. Verified anon → 3 public communities (cibc/nsrt/scenius); a real token decodes with the correct `iss` + slug memberships; JWKS live. The private-gating reveal is not demonstrable in prod (no private community has a Telegram `group_id`) — proven by tests + review, to be exercised in S3.
- **Next:** S3 — MC/DN email sign-in send Bearer tokens, exercising this gating end-to-end with real data.
