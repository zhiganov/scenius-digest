from datetime import datetime
from database import get_unpublished_links, mark_as_published


def generate_weekly_digest() -> tuple[str, list[int]]:
    """
    Generate a weekly digest of links.
    Returns the formatted message and list of link IDs included.
    """
    links = get_unpublished_links(since_days=7)

    if not links:
        return None, []

    # Group by topic
    links_by_topic = {"links": [], "memes": []}
    for link in links:
        topic = link["topic"]
        if topic in links_by_topic:
            links_by_topic[topic].append(link)

    # Build digest message
    today = datetime.now().strftime("%B %d, %Y")

    parts = [
        f"🔗 Weekly Links Digest",
        f"🗓 Week of {today}",
        ""
    ]

    # Links section
    if links_by_topic["links"]:
        parts.append("📚 From the Links topic:")
        parts.append("")
        for link in links_by_topic["links"][:10]:  # Max 10 links
            title = link["title"] or link["url"]
            shared_by = f" (via {link['shared_by']})" if link["shared_by"] else ""
            parts.append(f"• {title}{shared_by}")
            if link["description"]:
                parts.append(f"  {link['description'][:100]}...")
            parts.append(f"  {link['url']}")
            parts.append("")

    # Memes section
    if links_by_topic["memes"]:
        parts.append("🎭 From Memes & Delight:")
        parts.append("")
        for link in links_by_topic["memes"][:5]:  # Max 5 memes
            title = link["title"] or "Meme"
            shared_by = f" (via {link['shared_by']})" if link["shared_by"] else ""
            parts.append(f"• {title}{shared_by}")
            parts.append(f"  {link['url']}")
            parts.append("")

    if len(parts) <= 3:  # Only header, no content
        return None, []

    parts.append("Curated from our community conversations ✨")

    message = "\n".join(parts)
    link_ids = [link["id"] for link in links]

    return message, link_ids


def format_digest_narrative(links: list) -> str:
    """
    Format links into an engaging narrative style digest.
    This can be enhanced with AI summarization later.
    """
    if not links:
        return None

    # Group by topic
    links_topics = {"links": [], "memes": []}
    for link in links:
        if link["topic"] in links_topics:
            links_topics[link["topic"]].append(link)

    today = datetime.now().strftime("%B %d, %Y")

    parts = [
        f"🔗 Weekly Links Digest",
        f"🗓 Week of {today}",
        "",
        f"This week our community shared {len(links)} gems across Links and Memes & Delight. Here are the highlights:",
        ""
    ]

    if links_topics["links"]:
        parts.append("📚 Worth Reading:")
        for link in links_topics["links"][:8]:
            url = link["url"]
            title = link.get("title") or url
            parts.append(f"• {title}")
            parts.append(f"  {url}")
        parts.append("")

    if links_topics["memes"]:
        parts.append("🎭 Memes & Delight:")
        for link in links_topics["memes"][:4]:
            url = link["url"]
            parts.append(f"• {url}")
        parts.append("")

    return "\n".join(parts)
