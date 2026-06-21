import csv
import logging
from datetime import datetime
from io import StringIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.analysis import Analysis
from app.models.post import Post


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["export"])


@router.get("/csv")
def export_csv(
    platform: str | None = None,
    category: str | None = None,
    sentiment: str | None = None,
    language: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    try:
        statement = (
            select(Post)
            .outerjoin(Analysis, Analysis.post_id == Post.id)
            .options(selectinload(Post.analysis))
        )
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

        statement = statement.order_by(Post.posted_at.desc().nullslast(), Post.collected_at.desc())
        posts = db.scalars(statement).all()

        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "platform",
                "title",
                "content",
                "summary",
                "category",
                "sentiment",
                "language",
                "created_at",
                "url",
            ],
        )
        writer.writeheader()

        for post in posts:
            analysis = post.analysis
            row = {
                "platform": post.platform,
                "title": (post.title or "").replace("\n", " ").replace("\r", " "),
                "content": (post.content or "").replace("\n", " ").replace("\r", " "),
                "summary": (analysis.summary or "").replace("\n", " ").replace("\r", " ") if analysis else "",
                "category": analysis.category if analysis else "",
                "sentiment": analysis.sentiment if analysis else "",
                "language": analysis.language if analysis else "",
                "created_at": post.posted_at.isoformat() if post.posted_at else "",
                "url": post.url or "",
            }
            writer.writerow(row)

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=passport_posts.csv"},
        )

    except SQLAlchemyError:
        logger.exception("Failed to export CSV")
        raise
