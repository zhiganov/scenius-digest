# Events Aggregation for Participation Opportunities

*2026-02-08*

## Context

The My Community (MC) and Dear Neighbors (DN) Chrome extensions have a "participation opportunities" panel that currently shows Harmonica sessions (from Supabase) and Luma events (fetched client-side in MC only). We need to support more event sources — starting with Telegram event links from community groups — and unify them behind a single API.

This design also adds the NSRT community group to scenius-digest.

## Design Decisions

- **scenius-digest becomes the events API** — it already serves community metadata to MC via `/api/groups` and is the natural place to aggregate events from multiple sources.
- **Three event sources** (A now, B now, C future):
  - **A: Telegram event links** — shared by community members in event topics, stored in `digest_links` with OG + platform enrichment
  - **B: External event APIs** — Luma first, extensible to Meetup, partner APIs. Config-driven per community. Fetched live, not stored.
  - **C: Community-admin panel** (future) — manually curated opportunities. Will plug into the same endpoint when built.
- **OG + known platform detection** for Telegram links — always fetch OG metadata, then extract structured event data (datetime, location) from Luma API, Meetup ld+json, Eventbrite ld+json.
- **Two filtering paths**: MC filters by community, DN filters by city.

## New Community: NSRT

Add to `groups.json`:

```json
{
  "nsrt": {
    "name": "Novi Sad Relational Tech",
    "group_id": "-1003669626939",
    "output_channel": "-1003857482838",
    "city": "novi-sad",
    "topics": {
      "links": "16",
      "events": "8"
    },
    "event_topics": ["events"],
    "event_apis": [
      { "type": "luma", "url": "https://lu.ma/nsrt" }
    ]
  }
}
```

New fields for all groups:
- `city` (string) — city slug for DN filtering
- `event_topics` (string[]) — topic keys whose links are tagged as events
- `event_apis` (object[]) — external event API configs, each with `type` and `url`

## Database Changes

Three new nullable columns on `digest_links`:

```sql
ALTER TABLE digest_links ADD COLUMN type TEXT DEFAULT 'link';
ALTER TABLE digest_links ADD COLUMN event_starts_at TIMESTAMPTZ;
ALTER TABLE digest_links ADD COLUMN event_location TEXT;
```

- `type`: `'link'` (default) or `'event'` — set based on whether the message came from an `event_topics` topic
- `event_starts_at`: extracted from known platform APIs/ld+json, null if unknown
- `event_location`: extracted location string, null if unknown

## Webhook Enhancement

When `api/webhook.py` receives a link:

1. Determine if the source topic is in `event_topics` for that group → set `type = 'event'`
2. Fetch OG metadata (existing behavior)
3. If `type = 'event'` and URL matches a known platform, extract structured data:

### Platform Detection

**Luma** (`lu.ma/*` or `luma.com/*`):
- Extract slug from URL
- Call `https://api.lu.ma/event/get?event_api_id={slug}`
- Extract: `start_at`, `end_at`, `geo_address_info.full_address`

**Meetup** (`meetup.com/*/events/*`):
- Parse `application/ld+json` with `@type: "Event"` from the HTML already fetched for OG
- Extract: `startDate`, `endDate`, `location.name` + `location.address.streetAddress`

**Eventbrite** (`eventbrite.com/e/*`):
- Same approach — parse `ld+json` Event schema
- Extract: `startDate`, `endDate`, `location.name`

If extraction fails, fields stay null. The event still renders with OG preview.

### Implementation

New module `lib/event_enrichment.py`:

```python
def detect_platform(url: str) -> str | None:
    """Returns 'luma', 'meetup', 'eventbrite', or None."""

def enrich_event(url: str, html: str) -> dict:
    """Returns {'starts_at': ..., 'ends_at': ..., 'location': ...} or empty dict.
    For Luma: calls API. For Meetup/Eventbrite: parses ld+json from html."""
```

Called from `webhook.py` after OG fetch, only when `type = 'event'`.

## New Endpoint: `api/events.py`

`GET /api/events` — returns events from all sources, merged and deduplicated.

### Filters

| Param | Used by | Behavior |
|-------|---------|----------|
| `community` | MC | Events from one community (both Telegram + external APIs) |
| `city` | DN | Events from all communities in that city |
| (none) | — | All events from all visible communities |

### Sources Merged

1. **Telegram event links**: query `digest_links WHERE type = 'event'`, filtered by group
2. **External event APIs**: for each matching community with `event_apis`, call fetchers (Luma, etc.)
3. **(Future) Admin panel**: additional query to admin-managed opportunities table

### Deduplication

If a Telegram-sourced event URL matches an external API event URL, prefer the external API version (richer data). Deduplicate by normalized URL.

### Response Shape

```json
{
  "events": [
    {
      "id": "luma-abc123",
      "title": "NSRT Monthly Meetup",
      "description": "Monthly gathering...",
      "image": "https://...",
      "url": "https://lu.ma/nsrt-meetup",
      "starts_at": "2026-02-15T18:00:00Z",
      "ends_at": "2026-02-15T20:00:00Z",
      "location": "Novi Sad, Serbia",
      "source": "luma",
      "community": "nsrt"
    },
    {
      "id": "tg-4521",
      "title": "AI in Healthcare Workshop",
      "description": "Join us for...",
      "image": "https://og-image...",
      "url": "https://meetup.com/...",
      "starts_at": "2026-02-20T17:00:00Z",
      "ends_at": null,
      "location": "Startit Centar, Novi Sad",
      "source": "telegram",
      "community": "nsrt"
    }
  ]
}
```

Sorted by `starts_at` ascending. Events without `starts_at` go at the end.

### Luma Fetcher

New module `lib/luma.py`:

```python
def fetch_luma_events(calendar_url: str, community_key: str) -> list[dict]:
    """Fetches future events from a Luma calendar.
    Extracts slug from URL, calls api.lu.ma/calendar/get-items.
    Returns list of normalized event dicts."""
```

This replaces the client-side Luma fetching currently in MC's `lib/luma.js`.

## Extension Changes

### My Community

- `loadOpportunities(selectedCommunities)` replaces `loadSessions()`:
  1. For each selected community: `GET /api/events?community={key}`
  2. Plus: Supabase `sessions_with_topics` (Harmonica sessions, kept as fallback until Source C exists)
  3. Merge, deduplicate, sort by `starts_at`
- Remove `lib/luma.js` — Luma fetching moves server-side
- Rename `SessionsPanel` → `OpportunitiesPanel`
- Cards adapt based on available data
- `source` field shown as subtle badge (Luma, Telegram, Session)

### Dear Neighbors

- `loadOpportunities(city)` replaces `loadSessions()`:
  1. `GET /api/events?city={city}`
  2. Plus: Supabase sessions filtered by neighborhood (existing)
  3. Merge, sort
- Rename `SessionsPanel` → `OpportunitiesPanel`
- Same card design logic as MC

### Card Display Logic

| Data available | Card renders |
|---|---|
| `starts_at` + `location` | Date/time, location, title, description, image, source badge |
| `starts_at` only | Date/time, title, description, image, source badge |
| OG metadata only (no datetime) | Title, description, image — preview card style, no datetime row |

All cards link to `url`.

## Implementation Sequence

### Phase 1: scenius-digest backend
1. Add NSRT to `groups.json` with new fields (`city`, `event_topics`, `event_apis`)
2. Add `city`, `event_topics`, `event_apis` fields to existing groups (scenius, cibc)
3. Add columns to `digest_links` (`type`, `event_starts_at`, `event_location`)
4. Update `api/groups.py` to return new fields
5. Create `lib/event_enrichment.py` (platform detection + enrichment)
6. Update `api/webhook.py` to tag event links and enrich them
7. Create `lib/luma.py` (Luma calendar fetcher)
8. Create `api/events.py` endpoint
9. Deploy to Vercel
10. Register NSRT webhook with Telegram

### Phase 2: My Community extension
1. Add `loadOpportunities()` to sessions store (calls `/api/events` + Supabase)
2. Remove `lib/luma.js`
3. Rename `SessionsPanel` → `OpportunitiesPanel`
4. Update card component for new data shape
5. Test with NSRT + existing communities

### Phase 3: Dear Neighbors extension
1. Add `loadOpportunities(city)` to sessions store
2. Add city selection to settings (or derive from neighborhood)
3. Rename `SessionsPanel` → `OpportunitiesPanel`
4. Same card updates as MC

### Future: Source C (community-admin)
- Build admin panel with opportunities table
- scenius-digest `/api/events` reads from it as a third source
- Extensions don't change — they already consume the unified API
