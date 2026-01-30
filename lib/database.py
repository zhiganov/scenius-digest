import os
from datetime import datetime, timedelta, timezone
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")  # scenius-digest project
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def add_link(url: str, topic: str, shared_by: str = None, title: str = None,
             description: str = None, message_id: int = None, message_text: str = None,
             group_id: str = None, group_name: str = None) -> bool:
    """Add a new link. Returns False if duplicate (same URL in same group within 7 days)."""
    client = get_client()
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    # Check for duplicates
    query = client.table("digest_links").select("id").eq("url", url).gte("shared_at", since)
    if group_id:
        query = query.eq("group_id", group_id)

    result = query.execute()
    if result.data:
        return False

    client.table("digest_links").insert({
        "url": url,
        "title": title,
        "description": description,
        "group_id": group_id,
        "group_name": group_name,
        "topic": topic,
        "shared_by": shared_by,
        "message_id": message_id,
        "message_text": message_text,
    }).execute()

    return True


def get_unpublished_links(since_days: int = 7, group_id: str = None) -> list[dict]:
    """Get unpublished links from the last N days, optionally filtered by group."""
    client = get_client()
    since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()

    query = (
        client.table("digest_links")
        .select("*")
        .eq("published", False)
        .gte("shared_at", since)
        .order("topic")
        .order("shared_at", desc=True)
    )

    if group_id:
        query = query.eq("group_id", group_id)

    result = query.execute()
    return result.data


def get_links_by_group(group_id: str, since_days: int = 7, published: bool = None) -> list[dict]:
    """Get links for a specific group."""
    client = get_client()
    since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()

    query = (
        client.table("digest_links")
        .select("*")
        .eq("group_id", group_id)
        .gte("shared_at", since)
        .order("topic")
        .order("shared_at", desc=True)
    )

    if published is not None:
        query = query.eq("published", published)

    result = query.execute()
    return result.data


def mark_as_published(link_ids: list) -> None:
    """Mark links as published."""
    if not link_ids:
        return
    client = get_client()
    client.table("digest_links").update({"published": True}).in_("id", link_ids).execute()


def get_stats(group_id: str = None) -> dict:
    """Get link statistics, optionally for a specific group."""
    client = get_client()

    base = client.table("digest_links").select("id", count="exact")
    if group_id:
        base = base.eq("group_id", group_id)

    total = base.execute().count or 0

    unpub_q = client.table("digest_links").select("id", count="exact").eq("published", False)
    if group_id:
        unpub_q = unpub_q.eq("group_id", group_id)
    unpublished = unpub_q.execute().count or 0

    return {"total": total, "unpublished": unpublished, "published": total - unpublished}
