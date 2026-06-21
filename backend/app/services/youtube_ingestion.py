import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.post import Post
from app.models.scrape_run import ScrapeRun
from app.scrapers.api_sources.youtube import YOUTUBE_SEARCH_KEYWORDS, YouTubeScraper
from app.scrapers.api_sources.youtube.normalizer import normalize_youtube_video


logger = logging.getLogger(__name__)


class YouTubeIngestionService:
    def __init__(self, scraper: YouTubeScraper | None = None) -> None:
        self.scraper = scraper or YouTubeScraper()

    def ingest(
        self,
        keywords: Iterable[str] = YOUTUBE_SEARCH_KEYWORDS,
        max_results_per_keyword: int = 25,
        region_code: str | None = None,
    ) -> ScrapeRun:
        keyword_list = list(keywords)
        started_at = datetime.now(UTC)

        # Step 1: Collect all data first (NO DB SESSION OPENED YET)
        videos = self.scraper.search(
            keywords=keyword_list,
            max_results_per_keyword=max_results_per_keyword,
            region_code=region_code,
        )

        # Step 2: Now open a FRESH DB session for persistence
        logger.info("Opening fresh database session for persistence")
        db = SessionLocal()
        try:
            scrape_run = ScrapeRun(
                platform="youtube",
                source_type="api",
                query=", ".join(keyword_list),
                status="running",
                started_at=started_at,
                posts_found=len(videos),
                posts_saved=0,
            )
            db.add(scrape_run)
            db.commit()
            db.refresh(scrape_run)

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
                saved_count += self._insert_post_if_new(db, normalized, scrape_run.id)

            scrape_run.posts_saved = saved_count
            scrape_run.status = "success"
            scrape_run.finished_at = datetime.now(UTC)
            db.commit()
            db.refresh(scrape_run)
            logger.info("YouTube ingestion completed: found=%s saved=%s", scrape_run.posts_found, saved_count)
            return scrape_run

        except Exception as exc:
            logger.exception("YouTube ingestion failed")
            db.rollback()
            # Create scrape run for failed case
            scrape_run = ScrapeRun(
                platform="youtube",
                source_type="api",
                query=", ".join(keyword_list),
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                posts_found=len(videos),
                posts_saved=0,
                error_message=str(exc),
            )
            db.add(scrape_run)
            db.commit()
            db.refresh(scrape_run)
            return scrape_run
        finally:
            db.close()

    def _insert_post_if_new(self, db: Session, normalized: dict[str, Any], scrape_run_id) -> int:
        try:
            existing_post = db.scalar(
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

            db.add(Post(scrape_run_id=scrape_run_id, **normalized))
            return 1

        except SQLAlchemyError:
            logger.exception(
                "Failed to save YouTube video platform_post_id=%s",
                normalized.get("platform_post_id"),
            )
            raise
