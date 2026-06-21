import logging
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.services.google_news_ingestion import GoogleNewsIngestionService
from app.services.youtube_ingestion import YouTubeIngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    db = SessionLocal()
    try:
        logger.info("=== Running Google News Ingestion ===")
        google_news_service = GoogleNewsIngestionService(db)
        google_news_run = google_news_service.ingest()
        print("\nGoogle News Ingestion:")
        print(f"  posts_found: {google_news_run.posts_found}")
        print(f"  posts_saved: {google_news_run.posts_saved}")
        print(f"  status: {google_news_run.status}")
        if google_news_run.error_message:
            print(f"  error: {google_news_run.error_message}")

        logger.info("\n=== Running YouTube Ingestion ===")
        youtube_service = YouTubeIngestionService(db)
        youtube_run = youtube_service.ingest()
        print("\nYouTube Ingestion:")
        print(f"  posts_found: {youtube_run.posts_found}")
        print(f"  posts_saved: {youtube_run.posts_saved}")
        print(f"  status: {youtube_run.status}")
        if youtube_run.error_message:
            print(f"  error: {youtube_run.error_message}")

    except Exception as e:
        logger.exception("Manual ingestion failed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
