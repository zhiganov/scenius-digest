from datetime import datetime
from lib.database import get_unpublished_links

# Topic display names and emoji mappings
TOPIC_CONFIG = {
    "links": {"emoji": "📚", "display": "Links"},
    "memes": {"emoji": "🎭", "display": "Memes & Delight"},
    "news": {"emoji": "📰", "display": "News"},
    "resources": {"emoji": "📚", "display": "Resources"},
}


def get_topic_display(topic: str) -> tuple[str, str]:
    """Get emoji and display name for a topic."""
    config = TOPIC_CONFIG.get(topic, {"emoji": "📌", "display": topic.title()})
    return config["emoji"], config["display"]


def generate_weekly_digest(group_id: str = None, group_name: str = None) -> tuple[str, list[int]]:
    """
    Generate a weekly digest of links for a specific group.
    Returns the formatted message and list of link IDs included.
    """
    links = get_unpublished_links(since_days=7, group_id=group_id)

    if not links:
        return None, []

    # Group by topic
    links_by_topic = {}
    for link in links:
        topic = link["topic"]
        if topic not in links_by_topic:
            links_by_topic[topic] = []
        links_by_topic[topic].append(link)

    today = datetime.now().strftime("%B %d, %Y")

    header = "Weekly Links Digest"
    if group_name:
        header = f"{group_name} Links Digest"

    parts = [
        f"🔗 {header}",
        f"🗓 Week of {today}",
        ""
    ]

    for topic, topic_links in links_by_topic.items():
        if not topic_links:
            continue

        emoji, display_name = get_topic_display(topic)
        max_links = 5 if topic == "memes" else 10

        parts.append(f"{emoji} From {display_name}:")
        parts.append("")

        for link in topic_links[:max_links]:
            title = link["title"] or link["url"]
            shared_by = f" (via {link['shared_by']})" if link["shared_by"] else ""
            parts.append(f"• {title}{shared_by}")
            if link["description"]:
                parts.append(f"  {link['description'][:100]}...")
            parts.append(f"  {link['url']}")
            parts.append("")

    if len(parts) <= 3:
        return None, []

    parts.append("Curated from our community conversations ✨")

    message = "\n".join(parts)
    link_ids = [link["id"] for link in links]

    return message, link_ids
