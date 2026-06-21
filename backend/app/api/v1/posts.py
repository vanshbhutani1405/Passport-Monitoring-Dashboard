
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.analysis import Analysis
from app.models.post import Post
from app.nlp.groq_analyzer import GroqAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/posts", tags=["posts"])


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language: str
    category: str
    sentiment: str
    summary: str | None
    is_gibberish: bool
    is_duplicate: bool


class PostListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform: str
    platform_post_id: str
    title: str | None
    content: str
    url: str | None
    author_name: str | None
    content_type: str
    posted_at: datetime | None
    collected_at: datetime
    like_count: int
    comment_count: int
    share_count: int
    view_count: int
    analysis: AnalysisResponse | None = None


class PostDetail(PostListItem):
    author_url: str | None


class PaginatedPostsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PostListItem]


@router.get("", response_model=PaginatedPostsResponse)
def list_posts(
    platform: str | None = None,
    category: str | None = None,
    sentiment: str | None = None,
    language: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedPostsResponse:
    try:
        statement = (
            select(Post)
            .outerjoin(Analysis, Analysis.post_id == Post.id)
            .options(selectinload(Post.analysis))
        )
        statement = _apply_post_filters(
            statement=statement,
            platform=platform,
            category=category,
            sentiment=sentiment,
            language=language,
            start_date=start_date,
            end_date=end_date,
        )

        total = db.execute(select(func.count()).select_from(statement.subquery())).scalar() or 0
        posts = db.scalars(
            statement.order_by(Post.posted_at.desc().nullslast(), Post.collected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedPostsResponse(total=total, page=page, page_size=page_size, items=list(posts))
    except SQLAlchemyError:
        logger.exception("Failed to list posts")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")


@router.get("/{post_id}", response_model=PostDetail)
def get_post(post_id: UUID, db: Session = Depends(get_db)) -> Post:
    try:
        post = db.scalar(
            select(Post)
            .where(Post.id == post_id)
            .options(selectinload(Post.analysis))
        )
    except SQLAlchemyError:
        logger.exception(f"Failed to fetch post_id={post_id}")
        raise HTTPException(status_code=500, detail="Failed to fetch post")

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@router.post("/{post_id}/analyze", response_model=AnalysisResponse)
def analyze_post(post_id: UUID, db: Session = Depends(get_db)) -> Analysis:
    try:
        # Check if analysis already exists
        existing_analysis = db.scalar(
            select(Analysis).where(Analysis.post_id == post_id)
        )
        if existing_analysis:
            logger.info(f"Returning existing analysis for post_id={post_id}")
            return existing_analysis

        # Get post
        post = db.scalar(
            select(Post).where(Post.id == post_id)
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Generate analysis
        analyzer = GroqAnalyzer()
        content = "\n\n".join([post.title or "", post.content or ""])
        result = analyzer.analyze(content)

        # Save analysis
        analysis = Analysis(
            post_id=post_id,
            language=result.language,
            category=result.category,
            sentiment=result.sentiment,
            summary=result.summary,
            is_gibberish=result.is_gibberish,
            is_duplicate=False,
            analyzed_at=datetime.now(timezone.utc),
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        logger.info(f"Created new analysis for post_id={post_id}")
        return analysis
    except HTTPException:
        raise
    except SQLAlchemyError:
        logger.exception(f"Failed to analyze post_id={post_id}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to analyze post")
    except Exception as e:
        logger.exception(f"Unexpected error analyzing post_id={post_id}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to analyze post")


def _apply_post_filters(
    statement,
    platform: str | None,
    category: str | None,
    sentiment: str | None,
    language: str | None,
    start_date: datetime | None,
    end_date: datetime | None,
):
    if platform:
        statement = statement.where(Post.platform == platform)
    if category:
        statement = statement.where(Analysis.category == category)
    if sentiment:
        statement = statement.where(Analysis.sentiment == sentiment)
    if language:
        statement = statement.where(Analysis.language == language)
    if start_date:
        statement = statement.where(Post.posted_at >= start_date)
    if end_date:
        statement = statement.where(Post.posted_at <= end_date)
    return statement

