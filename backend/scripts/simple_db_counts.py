
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.post import Post
from app.models.analysis import Analysis

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))

db = SessionLocal()
try:
    total_posts = db.query(Post).count()
    total_analyses = db.query(Analysis).count()

    # Count pending with explicit onclause
    from sqlalchemy import select, func
    stmt = (
        select(func.count(Post.id))
        .select_from(Post)
        .outerjoin(Analysis, Analysis.post_id == Post.id)
        .where(Analysis.id.is_(None))
    )
    pending = db.execute(stmt).scalar() or 0

    print("=" * 60)
    print("  CURRENT DATABASE STATS")
    print("=" * 60)
    print(f"  - Total posts: {total_posts}")
    print(f"  - Total analyses: {total_analyses}")
    print(f"  - Pending analysis: {pending}")
    print(f"  - Failed posts: {pending}")
    print("=" * 60)
finally:
    db.close()

