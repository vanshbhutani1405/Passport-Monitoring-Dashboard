import logging
import feedparser
from urllib.parse import quote
from typing import Any
from collections.abc import Iterable

logger = logging.getLogger(__name__)

GOOGLE_NEWS_SEARCH_KEYWORDS = [
    "passport",
    "passport renewal",
    "passport application",
    "passport delay",
    "passport visa",
]


class GoogleNewsScraper:
    def __init__(self):
        pass

    def search(
        self,
        keywords: Iterable[str] = GOOGLE_NEWS_SEARCH_KEYWORDS,
    ) -> list[dict[str, Any]]:
        articles = []

        for keyword in keywords:
            try:
                logger.info("Searching Google News for keyword=%s", keyword)
                rss_url = f"https://news.google.com/rss/search?q={quote(keyword)}&hl=en-US&gl=US&ceid=US:en"
                feed = feedparser.parse(rss_url)

                for entry in feed.entries:
                    article = {
                        "title": entry.get("title"),
                        "description": entry.get("summary", ""),
                        "source": entry.get("source", {}).get("title"),
                        "url": entry.get("link"),
                        "published": entry.get("published"),
                        "published_parsed": entry.get("published_parsed"),
                    }
                    articles.append(article)
            except Exception:
                logger.exception("Google News search failed for keyword=%s", keyword)
                raise

        return articles
