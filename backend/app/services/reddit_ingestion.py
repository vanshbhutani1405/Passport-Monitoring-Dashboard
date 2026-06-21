import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.scrape_run import ScrapeRun
from app.scrapers.api_sources.reddit import REDDIT_SEARCH_KEYWORDS, RedditScraper
from app.scrapers.api_sources.reddit.normalizer import normalize_reddit_submission


logger = logging.getLogger(__name__)


class RedditIngestionService:
    def __init__(self, db: Session, scraper: RedditScraper | None = None) -> None:
        self.db = db
        self.scraper = scraper or RedditScraper()

    def ingest(
        self,
        keywords: Iterable[str] = REDDIT_SEARCH_KEYWORDS,
        limit_per_keyword: int = 25,
        subreddit: str = "all",
    ) -> ScrapeRun:
        keyword_list = list(keywords)
        scrape_run = ScrapeRun(
            platform="reddit",
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
            submissions = self.scraper.search(
                keywords=keyword_list,
                limit_per_keyword=limit_per_keyword,
                subreddit=subreddit,
            )
            scrape_run.posts_found = len(submissions)

            saved_count = 0
            seen_keys: set[tuple[str, str]] = set()

            for submission in submissions:
                normalized = normalize_reddit_submission(submission)
                platform_post_id = normalized.get("platform_post_id")
                if not platform_post_id:
                    logger.warning("Skipping Reddit submission without platform_post_id")
                    continue

                unique_key = (normalized["platform"], platform_post_id)
                if unique_key in seen_keys:
                    continue

                seen_keys.add(unique_key)
                saved_count += self._upsert_post(normalized, scrape_run.id)

            scrape_run.posts_saved = saved_count
            scrape_run.status = "success"
            scrape_run.finished_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(scrape_run)
            logger.info("Reddit ingestion completed: found=%s saved=%s", scrape_run.posts_found, saved_count)
            return scrape_run

        except Exception as exc:
            logger.exception("Reddit ingestion failed")
            self.db.rollback()
            scrape_run.status = "failed"
            scrape_run.finished_at = datetime.now(UTC)
            scrape_run.error_message = str(exc)
            self.db.add(scrape_run)
            self.db.commit()
            self.db.refresh(scrape_run)
            return scrape_run

    def _upsert_post(self, normalized: dict[str, Any], scrape_run_id) -> int:
        try:
            existing_post = self.db.scalar(
                select(Post).where(
                    Post.platform == normalized["platform"],
                    Post.platform_post_id == normalized["platform_post_id"],
                )
            )

            if existing_post:
                self._update_existing_post(existing_post, normalized, scrape_run_id)
                return 0

            self.db.add(Post(scrape_run_id=scrape_run_id, **normalized))
            return 1

        except SQLAlchemyError:
            logger.exception(
                "Failed to save Reddit post platform_post_id=%s",
                normalized.get("platform_post_id"),
            )
            raise

    @staticmethod
    def _update_existing_post(post: Post, normalized: dict[str, Any], scrape_run_id) -> None:
        post.scrape_run_id = scrape_run_id
        post.url = normalized["url"]
        post.title = normalized["title"]
        post.content = normalized["content"]
        post.author_name = normalized["author_name"]
        post.author_url = normalized["author_url"]
        post.posted_at = normalized["posted_at"]
        post.collected_at = normalized["collected_at"]
        post.like_count = normalized["like_count"]
        post.comment_count = normalized["comment_count"]
        post.share_count = normalized["share_count"]
        post.view_count = normalized["view_count"]
        post.raw_data = normalized["raw_data"]
