import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyses"

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    language: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    is_gibberish: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))
    embedding_model: Mapped[str | None] = mapped_column(String(100))
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    duplicate_of_post_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="SET NULL"),
    )
    duplicate_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    post = relationship("Post", back_populates="analysis", foreign_keys=[post_id])
    duplicate_of_post = relationship(
        "Post",
        back_populates="duplicate_analyses",
        foreign_keys=[duplicate_of_post_id],
    )

    __table_args__ = (
        Index("ix_analyses_category_sentiment", "category", "sentiment"),
        Index("ix_analyses_language_category", "language", "category"),
        Index(
            "ix_analyses_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
