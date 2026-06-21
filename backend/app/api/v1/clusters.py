import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cluster import Cluster
from app.models.cluster_membership import ClusterMembership
from app.models.post import Post


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clusters", tags=["clusters"])


class ClusterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    dominant_category: str | None
    dominant_sentiment: str | None
    post_count: int
    created_at: datetime
    updated_at: datetime


class ClusterPostResponse(BaseModel):
    id: UUID
    platform: str
    title: str | None
    content: str
    url: str | None
    posted_at: datetime | None
    similarity_score: float | None


class PaginatedClustersResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ClusterResponse]


class PaginatedClusterPostsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ClusterPostResponse]


@router.get("", response_model=PaginatedClustersResponse)
def list_clusters(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedClustersResponse:
    try:
        statement = select(Cluster)
        total = db.scalar(select(func.count()).select_from(Cluster)) or 0
        clusters = db.scalars(
            statement.order_by(Cluster.post_count.desc(), Cluster.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return PaginatedClustersResponse(total=total, page=page, page_size=page_size, items=list(clusters))
    except SQLAlchemyError:
        logger.exception("Failed to list clusters")
        raise HTTPException(status_code=500, detail="Failed to fetch clusters")


@router.get("/{cluster_id}", response_model=ClusterResponse)
def get_cluster(cluster_id: UUID, db: Session = Depends(get_db)) -> Cluster:
    try:
        cluster = db.get(Cluster, cluster_id)
    except SQLAlchemyError:
        logger.exception("Failed to fetch cluster_id=%s", cluster_id)
        raise HTTPException(status_code=500, detail="Failed to fetch cluster")

    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    return cluster


@router.get("/{cluster_id}/posts", response_model=PaginatedClusterPostsResponse)
def get_cluster_posts(
    cluster_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedClusterPostsResponse:
    try:
        if not db.get(Cluster, cluster_id):
            raise HTTPException(status_code=404, detail="Cluster not found")

        statement = (
            select(Post, ClusterMembership.similarity_score)
            .join(ClusterMembership, ClusterMembership.post_id == Post.id)
            .where(ClusterMembership.cluster_id == cluster_id)
        )
        total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        rows = db.execute(
            statement.order_by(ClusterMembership.similarity_score.desc().nullslast())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    except HTTPException:
        raise
    except SQLAlchemyError:
        logger.exception("Failed to fetch posts for cluster_id=%s", cluster_id)
        raise HTTPException(status_code=500, detail="Failed to fetch cluster posts")

    items = [
        ClusterPostResponse(
            id=post.id,
            platform=post.platform,
            title=post.title,
            content=post.content,
            url=post.url,
            posted_at=post.posted_at,
            similarity_score=float(similarity_score) if similarity_score is not None else None,
        )
        for post, similarity_score in rows
    ]
    return PaginatedClusterPostsResponse(total=total, page=page, page_size=page_size, items=items)
