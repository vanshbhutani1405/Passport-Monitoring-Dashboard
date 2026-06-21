import hashlib
from datetime import UTC, datetime
from typing import Any


def normalize_google_news_article(article: dict[str, Any]) -> dict[str, Any]:
    url = article.get("url")
    platform_post_id = hashlib.md5(url.encode("utf-8")).hexdigest() if url else None

    posted_at = None
    if article.get("published_parsed"):
        posted_at = datetime(*article["published_parsed"][:6], tzinfo=UTC)
    elif article.get("published"):
        try:
            posted_at = datetime.fromisoformat(article["published"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    return {
        "platform": "google_news",
        "platform_post_id": platform_post_id,
        "url": url,
        "title": article.get("title"),
        "content": article.get("description", ""),
        "author_name": article.get("source"),
        "author_url": None,
        "content_type": "article",
        "posted_at": posted_at,
        "collected_at": datetime.now(UTC),
        "like_count": 0,
        "comment_count": 0,
        "share_count": 0,
        "view_count": 0,
        "raw_data": article,
    }
