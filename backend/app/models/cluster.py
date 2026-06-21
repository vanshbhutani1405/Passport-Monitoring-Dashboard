from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Cluster(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clusters"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    dominant_category: Mapped[str | None] = mapped_column(String(50), index=True)
    dominant_sentiment: Mapped[str | None] = mapped_column(String(20), index=True)
    post_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    memberships = relationship(
        "ClusterMembership",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_clusters_category_sentiment", "dominant_category", "dominant_sentiment"),
    )
