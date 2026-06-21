from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Post(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "posts"

    scrape_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scrape_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    platform_post_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[str | None] = mapped_column(String(255))
    author_url: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    share_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    scrape_run = relationship("ScrapeRun", back_populates="posts")
    analysis = relationship(
        "Analysis",
        back_populates="post",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="Analysis.post_id",
    )
    translations = relationship(
        "Translation",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    cluster_memberships = relationship(
        "ClusterMembership",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    duplicate_analyses = relationship(
        "Analysis",
        back_populates="duplicate_of_post",
        foreign_keys="Analysis.duplicate_of_post_id",
    )

    __table_args__ = (
        UniqueConstraint("platform", "platform_post_id", name="uq_posts_platform_post_id"),
        Index("ix_posts_platform_posted_at", "platform", "posted_at"),
    )
