import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.analysis import Analysis
from app.models.cluster import Cluster
from app.models.post import Post


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


class CountItem(BaseModel):
    name: str
    count: int


class TopClusterItem(BaseModel):
    id: str
    name: str
    description: str | None
    dominant_category: str | None
    dominant_sentiment: str | None
    post_count: int
    created_at: datetime
    updated_at: datetime


class AnalyticsResponse(BaseModel):
    total_posts: int
    clusters_count: int
    posts_by_platform: list[CountItem]
    posts_by_sentiment: list[CountItem]
    posts_by_category: list[CountItem]
    top_categories: list[CountItem]
    top_clusters: list[TopClusterItem]


@router.get("", response_model=AnalyticsResponse)
def get_analytics(
    top_limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> AnalyticsResponse:
    try:
        total_posts = db.scalar(select(func.count()).select_from(Post)) or 0
        clusters_count = db.scalar(select(func.count()).select_from(Cluster)) or 0

        posts_by_platform = _count_grouped(db, Post.platform)
        posts_by_sentiment = _count_grouped(db, Analysis.sentiment)
        posts_by_category = _count_grouped(db, Analysis.category)
        top_categories = posts_by_category[:top_limit]
        top_clusters = db.scalars(
            select(Cluster)
            .order_by(Cluster.post_count.desc(), Cluster.created_at.desc())
            .limit(top_limit)
        ).all()

        return AnalyticsResponse(
            total_posts=total_posts,
            clusters_count=clusters_count,
            posts_by_platform=posts_by_platform,
            posts_by_sentiment=posts_by_sentiment,
            posts_by_category=posts_by_category,
            top_categories=top_categories,
            top_clusters=[
                TopClusterItem(
                    id=str(cluster.id),
                    name=cluster.name,
                    description=cluster.description,
                    dominant_category=cluster.dominant_category,
                    dominant_sentiment=cluster.dominant_sentiment,
                    post_count=cluster.post_count,
                    created_at=cluster.created_at,
                    updated_at=cluster.updated_at,
                )
                for cluster in top_clusters
            ],
        )
    except SQLAlchemyError:
        logger.exception("Failed to load analytics")
        raise HTTPException(status_code=500, detail="Failed to load analytics")


def _count_grouped(db: Session, column) -> list[CountItem]:
    rows = db.execute(
        select(column, func.count())
        .where(column.is_not(None))
        .group_by(column)
        .order_by(func.count().desc())
    ).all()
    return [CountItem(name=str(name), count=count) for name, count in rows]
