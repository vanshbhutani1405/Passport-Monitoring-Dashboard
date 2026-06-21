import logging
from dataclasses import dataclass

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.post import Post
from app.models.translation import Translation
from app.nlp.embedding_service import EMBEDDING_MODEL_NAME, EmbeddingService


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmbeddingWorkItem:
    analysis: Analysis
    text: str


class EmbeddingPipeline:
    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()

    def process_missing_embeddings(
        self,
        limit: int = 100,
        encode_batch_size: int = 32,
        target_language: str = "en",
    ) -> dict[str, int]:
        work_items = self._fetch_work_items(limit=limit, target_language=target_language)
        stats = {
            "found": len(work_items),
            "processed": 0,
            "failed": 0,
        }

        if not work_items:
            logger.info("No analyses found with missing embeddings")
            return stats

        logger.info(
            "Starting embedding batch: found=%s limit=%s encode_batch_size=%s",
            len(work_items),
            limit,
            encode_batch_size,
        )

        try:
            texts = [item.text for item in work_items]
            embeddings = self.embedding_service.embed_texts(
                texts,
                batch_size=encode_batch_size,
            )

            for item, embedding in zip(work_items, embeddings, strict=True):
                item.analysis.embedding = embedding
                item.analysis.embedding_model = EMBEDDING_MODEL_NAME
                stats["processed"] += 1

            self.db.commit()
            logger.info(
                "Embedding batch completed: found=%s processed=%s failed=%s",
                stats["found"],
                stats["processed"],
                stats["failed"],
            )
            return stats

        except Exception:
            stats["failed"] = stats["found"] - stats["processed"]
            logger.exception("Embedding batch failed")
            self.db.rollback()
            raise

    def _fetch_work_items(self, limit: int, target_language: str) -> list[EmbeddingWorkItem]:
        statement = (
            select(Analysis, Post, Translation)
            .join(Post, Post.id == Analysis.post_id)
            .outerjoin(
                Translation,
                and_(
                    Translation.post_id == Post.id,
                    Translation.target_language == target_language,
                ),
            )
            .where(Analysis.embedding.is_(None))
            .order_by(Post.collected_at.asc())
            .limit(limit)
        )

        try:
            rows = self.db.execute(statement).all()
        except SQLAlchemyError:
            logger.exception("Failed to fetch analyses with missing embeddings")
            raise

        work_items: list[EmbeddingWorkItem] = []
        for analysis, post, translation in rows:
            text = self._select_embedding_text(post=post, translation=translation)
            work_items.append(EmbeddingWorkItem(analysis=analysis, text=text))

        return work_items

    @staticmethod
    def _select_embedding_text(post: Post, translation: Translation | None) -> str:
        if translation:
            translated_parts = [
                translation.translated_title or "",
                translation.translated_content or "",
            ]
            translated_text = "\n\n".join(part for part in translated_parts if part.strip())
            if translated_text.strip():
                return translated_text

        original_parts = [
            post.title or "",
            post.content or "",
        ]
        return "\n\n".join(part for part in original_parts if part.strip())
