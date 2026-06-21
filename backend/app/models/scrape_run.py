from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ScrapeRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scrape_runs"

    platform: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    query: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    posts_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    posts_saved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    posts = relationship("Post", back_populates="scrape_run")

    __table_args__ = (
        Index("ix_scrape_runs_platform_started_at", "platform", "started_at"),
    )
