import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Translation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "translations"

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_language: Mapped[str] = mapped_column(String(20), nullable=False)
    target_language: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    translated_title: Mapped[str | None] = mapped_column(Text)
    translated_content: Mapped[str] = mapped_column(Text, nullable=False)
    translated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    post = relationship("Post", back_populates="translations")

    __table_args__ = (
        UniqueConstraint("post_id", "target_language", name="uq_translations_post_target_language"),
        Index("ix_translations_source_target_language", "source_language", "target_language"),
    )
