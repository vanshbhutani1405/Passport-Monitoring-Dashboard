import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.post import Post
from app.nlp.groq_analyzer import GroqAnalyzer


logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, db: Session, analyzer: GroqAnalyzer | None = None) -> None:
        self.db = db
        self.analyzer = analyzer or GroqAnalyzer()

    def process_unanalysed_posts(self, limit: int = 50) -> dict[str, int]:
        posts = self._fetch_unanalysed_posts(limit=limit)
        stats = {
            "found": len(posts),
            "processed": 0,
            "failed": 0,
        }

        logger.info("Starting Groq analysis batch: found=%s limit=%s", len(posts), limit)

        for post in posts:
            try:
                self.process_post(post)
                stats["processed"] += 1
            except Exception:
                stats["failed"] += 1
                logger.exception(
                    "Failed to analyse post_id=%s platform=%s platform_post_id=%s",
                    post.id,
                    post.platform,
                    post.platform_post_id,
                )
                self.db.rollback()

        logger.info(
            "Groq analysis batch completed: found=%s processed=%s failed=%s",
            stats["found"],
            stats["processed"],
            stats["failed"],
        )
        return stats

    def process_post(self, post: Post) -> Analysis:
        existing_analysis = self.db.scalar(select(Analysis).where(Analysis.post_id == post.id))
        if existing_analysis:
            logger.info("Skipping already analysed post_id=%s", post.id)
            return existing_analysis

        text = self._build_input_text(post)
        result = self.analyzer.analyze(text)

        analysis = Analysis(
            post_id=post.id,
            language=result.language,
            category=result.category,
            sentiment=result.sentiment,
            summary=result.summary,
            is_gibberish=result.is_gibberish,
            is_duplicate=False,
            analyzed_at=datetime.now(UTC),
        )

        try:
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            logger.info(
                "Stored Groq analysis post_id=%s category=%s sentiment=%s language=%s",
                post.id,
                analysis.category,
                analysis.sentiment,
                analysis.language,
            )
            return analysis
        except SQLAlchemyError:
            logger.exception("Failed to store analysis for post_id=%s", post.id)
            self.db.rollback()
            raise

    def _fetch_unanalysed_posts(self, limit: int) -> list[Post]:
        statement = (
            select(Post)
            .outerjoin(Analysis, Analysis.post_id == Post.id)
            .where(Analysis.id.is_(None))
            .order_by(Post.collected_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    @staticmethod
    def _build_input_text(post: Post) -> str:
        parts = [post.title or "", post.content or ""]
        return "\n\n".join(part for part in parts if part.strip())
