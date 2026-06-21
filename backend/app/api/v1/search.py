import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.analysis import Analysis
from app.models.post import Post
from app.models.translation import Translation


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


class SearchResultItem(BaseModel):
    id: UUID
    platform: str
    title: str | None
    content: str
    url: str | None
    posted_at: datetime | None
    category: str | None
    sentiment: str | None
    summary: str | None


class SearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SearchResultItem]


@router.get("", response_model=SearchResponse)
def search_posts(
    q: str = Query(min_length=1),
    platform: str | None = None,
    category: str | None = None,
    sentiment: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SearchResponse:
    try:
        pattern = f"%{q}%"
        statement = (
            select(Post)
            .outerjoin(Analysis, Analysis.post_id == Post.id)
            .outerjoin(Translation, Translation.post_id == Post.id)
            .where(
                or_(
                    Post.title.ilike(pattern),
                    Post.content.ilike(pattern),
                    Translation.translated_title.ilike(pattern),
                    Translation.translated_content.ilike(pattern),
                    Analysis.summary.ilike(pattern),
                )
            )
            .distinct()
            .options(selectinload(Post.analysis))
        )

        if category:
            statement = statement.where(Analysis.category == category)
        if sentiment:
            statement = statement.where(Analysis.sentiment == sentiment)
        if platform:
            statement = statement.where(Post.platform == platform)

        total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        posts = db.scalars(
            statement.order_by(Post.posted_at.desc().nullslast(), Post.collected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    except SQLAlchemyError:
        logger.exception(
            "Search failed query=%s platform=%s category=%s sentiment=%s",
            q,
            platform,
            category,
            sentiment,
        )
        raise HTTPException(status_code=500, detail="Search failed")

    items = [
        SearchResultItem(
            id=post.id,
            platform=post.platform,
            title=post.title,
            content=post.content,
            url=post.url,
            posted_at=post.posted_at,
            category=post.analysis.category if post.analysis else None,
            sentiment=post.analysis.sentiment if post.analysis else None,
            summary=post.analysis.summary if post.analysis else None,
        )
        for post in posts
    ]
    return SearchResponse(total=total, page=page, page_size=page_size, items=items)
