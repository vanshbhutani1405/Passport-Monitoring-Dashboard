import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.scrape_run import ScrapeRun
from app.scrapers.api_sources.youtube import YOUTUBE_SEARCH_KEYWORDS, YouTubeScraper
from app.scrapers.api_sources.youtube.normalizer import normalize_youtube_video


logger = logging.getLogger(__name__)


class YouTubeIngestionService:
    def __init__(self, db: Session, scraper: YouTubeScraper | None = None) -> None:
        self.db = db
        self.scraper = scraper or YouTubeScraper()

    def ingest(
        self,
        keywords: Iterable[str] = YOUTUBE_SEARCH_KEYWORDS,
        max_results_per_keyword: int = 25,
        region_code: str | None = None,
    ) -> ScrapeRun:
        keyword_list = list(keywords)
        scrape_run = ScrapeRun(
            platform="youtube",
            source_type="api",
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
            videos = self.scraper.search(
                keywords=keyword_list,
                max_results_per_keyword=max_results_per_keyword,
                region_code=region_code,
            )
            scrape_run.posts_found = len(videos)

            saved_count = 0
            seen_keys: set[tuple[str, str]] = set()

            for video in videos:
                normalized = normalize_youtube_video(video)
                platform_post_id = normalized.get("platform_post_id")
                if not platform_post_id:
                    logger.warning("Skipping YouTube video without platform_post_id")
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
            logger.info("YouTube ingestion completed: found=%s saved=%s", scrape_run.posts_found, saved_count)
            return scrape_run

        except Exception as exc:
            logger.exception("YouTube ingestion failed")
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
                    "Skipping duplicate YouTube video platform_post_id=%s",
                    normalized["platform_post_id"],
                )
                return 0

            self.db.add(Post(scrape_run_id=scrape_run_id, **normalized))
            return 1

        except SQLAlchemyError:
            logger.exception(
                "Failed to save YouTube video platform_post_id=%s",
                normalized.get("platform_post_id"),
            )
            raise
