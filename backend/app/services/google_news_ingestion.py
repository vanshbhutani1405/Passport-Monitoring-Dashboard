import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.scrape_run import ScrapeRun
from app.scrapers.rss_sources.google_news import (
    GOOGLE_NEWS_SEARCH_KEYWORDS,
    GoogleNewsScraper,
    normalize_google_news_article,
)

logger = logging.getLogger(__name__)


class GoogleNewsIngestionService:
    def __init__(self, db: Session, scraper: GoogleNewsScraper | None = None) -> None:
        self.db = db
        self.scraper = scraper or GoogleNewsScraper()

    def ingest(
        self,
        keywords: Iterable[str] = GOOGLE_NEWS_SEARCH_KEYWORDS,
    ) -> ScrapeRun:
        keyword_list = list(keywords)
        scrape_run = ScrapeRun(
            platform="google_news",
            source_type="rss",
            query=", ".join(keyword_list),
            status="running",
            started_at=datetime.now(UTC),
            posts_found=0,
            posts_saved=0,
        )
        self.db.add(scrape_run)
        self.db.commit()
        self.db.refresh(scrape_run)

        try:
            articles = self.scraper.search(
                keywords=keyword_list,
            )
            scrape_run.posts_found = len(articles)

            saved_count = 0
            seen_keys: set[tuple[str, str]] = set()

            for article in articles:
                normalized = normalize_google_news_article(article)
                platform_post_id = normalized.get("platform_post_id")
                if not platform_post_id:
                    logger.warning("Skipping Google News article without platform_post_id")
                    continue

                unique_key = (normalized["platform"], platform_post_id)
                if unique_key in seen_keys:
                    continue

                seen_keys.add(unique_key)
                saved_count += self._insert_post_if_new(normalized, scrape_run.id)

            scrape_run.posts_saved = saved_count
            scrape_run.status = "success"
            scrape_run.finished_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(scrape_run)
            logger.info("Google News ingestion completed: found=%s saved=%s", scrape_run.posts_found, saved_count)
            return scrape_run

        except Exception as exc:
            logger.exception("Google News ingestion failed")
            self.db.rollback()
            scrape_run.status = "failed"
            scrape_run.finished_at = datetime.now(UTC)
            scrape_run.error_message = str(exc)
            self.db.add(scrape_run)
            self.db.commit()
            self.db.refresh(scrape_run)
            return scrape_run

    def _insert_post_if_new(self, normalized: dict[str, Any], scrape_run_id) -> int:
        try:
            existing_post = self.db.scalar(
                select(Post).where(
                    Post.platform == normalized["platform"],
                    Post.platform_post_id == normalized["platform_post_id"],
                )
            )

            if existing_post:
                logger.info(
                    "Skipping duplicate Google News article platform_post_id=%s",
                    normalized["platform_post_id"],
                )
                return 0

            self.db.add(Post(scrape_run_id=scrape_run_id, **normalized))
            return 1

        except SQLAlchemyError:
            logger.exception(
                "Failed to save Google News article platform_post_id=%s",
                normalized.get("platform_post_id"),
            )
            raise
