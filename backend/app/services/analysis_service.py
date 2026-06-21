import logging
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.post import Post
from app.nlp.groq_analyzer import GroqAnalyzer
from app.core.config import get_settings


logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, db: Session, analyzer: GroqAnalyzer | None = None) -> None:
        self.db = db
        self.analyzer = analyzer or GroqAnalyzer()
        self.settings = get_settings()

    def process_unanalysed_posts(self, limit: int | None = None) -> dict[str, any]:
        if limit is None:
            limit = self.settings.analysis_batch_size
            
        total_pending = self.db.scalar(
            select(func.count())
            .select_from(Post)
            .outerjoin(Analysis, Analysis.post_id == Post.id)
            .where(Analysis.id.is_(None))
        ) or 0
        
        posts = self._fetch_unanalysed_posts(limit=limit)
        stats = {
            "total_pending": total_pending,
            "found": len(posts),
            "processed": 0,
            "failed": 0,
            "success": True,
        }

        logger.info("Starting Groq analysis batch: found=%s limit=%s total_pending=%s", len(posts), limit, total_pending)

        for idx, post in enumerate(posts, start=1):
            try:
                logger.info(f"Analyzing post {idx}/{len(posts)}")
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

        remaining = max(0, total_pending - stats["processed"])
        stats["remaining"] = remaining
        
        logger.info(
            "Groq analysis batch completed: found=%s processed=%s failed=%s remaining=%s",
            stats["found"],
            stats["processed"],
            stats["failed"],
            stats["remaining"],
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
            analyzed_at=datetime.now(timezone.utc),
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
        subquery = select(Analysis.post_id).subquery()
        statement = (
            select(Post)
            .where(Post.id.not_in(subquery))
            .order_by(Post.collected_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    @staticmethod
    def _build_input_text(post: Post) -> str:
        parts = [post.title or "", post.content or ""]
        return "\n\n".join(part for part in parts if part.strip())
