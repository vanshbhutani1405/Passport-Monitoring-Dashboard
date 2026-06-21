import uuid

from sqlalchemy import ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ClusterMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cluster_memberships"

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    similarity_score: Mapped[float | None] = mapped_column(Numeric(5, 4))

    cluster = relationship("Cluster", back_populates="memberships")
    post = relationship("Post", back_populates="cluster_memberships")

    __table_args__ = (
        UniqueConstraint("cluster_id", "post_id", name="uq_cluster_memberships_cluster_post"),
        Index("ix_cluster_memberships_cluster_similarity", "cluster_id", "similarity_score"),
    )
