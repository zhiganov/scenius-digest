"""Fetch Open Graph metadata from a URL using only stdlib."""

import re
import logging
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

# Match <meta property="og:..." content="..."> (handles single/double quotes, self-closing)
OG_PATTERN = re.compile(
    r'<meta\s+[^>]*?property=["\']og:(\w+)["\'][^>]*?content=["\']([^"\']*)["\']',
    re.IGNORECASE | re.DOTALL,
)

# Also match reverse order: content before property
OG_PATTERN_REV = re.compile(
    r'<meta\s+[^>]*?content=["\']([^"\']*)["\'][^>]*?property=["\']og:(\w+)["\']',
    re.IGNORECASE | re.DOTALL,
)

# Fallback: <title> tag
TITLE_PATTERN = re.compile(r'<title[^>]*>([^<]+)</title>', re.IGNORECASE)

# Fallback: <meta name="description" content="...">
DESC_PATTERN = re.compile(
    r'<meta\s+[^>]*?name=["\']description["\'][^>]*?content=["\']([^"\']*)["\']',
    re.IGNORECASE | re.DOTALL,
)


def fetch_og(url: str, timeout: int = 5) -> dict:
    """Fetch OG metadata from a URL. Returns dict with og_title, og_description, og_image.

    All values default to None on failure. Designed to be fast and never raise.
    """
    result = {"og_title": None, "og_description": None, "og_image": None}

    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; SceniusDigestBot/1.0)",
            "Accept": "text/html",
        })
        # Read only the first 32KB — OG tags are always in <head>
        with urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return result
            raw = resp.read(32768)

        html = raw.decode("utf-8", errors="replace")

        # Parse OG tags
        og = {}
        for match in OG_PATTERN.finditer(html):
            og[match.group(1)] = match.group(2)
        for match in OG_PATTERN_REV.finditer(html):
            og[match.group(2)] = match.group(1)

        result["og_title"] = _clean(og.get("title"))
        result["og_description"] = _clean(og.get("description"))
        result["og_image"] = og.get("image") or None

        # Fallbacks if OG tags missing
        if not result["og_title"]:
            m = TITLE_PATTERN.search(html)
            if m:
                result["og_title"] = _clean(m.group(1))

        if not result["og_description"]:
            m = DESC_PATTERN.search(html)
            if m:
                result["og_description"] = _clean(m.group(1))

    except (URLError, OSError, ValueError, UnicodeDecodeError) as e:
        logger.debug(f"OG fetch failed for {url}: {e}")

    return result


def _clean(text: str | None) -> str | None:
    """Strip whitespace and HTML entities, truncate."""
    if not text:
        return None
    text = text.strip()
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&#39;", "'").replace("&quot;", '"')
    if len(text) > 500:
        text = text[:497] + "..."
    return text or None
