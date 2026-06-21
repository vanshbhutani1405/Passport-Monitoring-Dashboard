
import logging
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.analysis import Analysis
from app.models.post import Post
from app.nlp.groq_analyzer import GroqAnalyzer


logger = logging.getLogger(__name__)


class AnalysisJobManager:
    _instance: Optional["AnalysisJobManager"] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.status: Dict[str, Any] = {
            "status": "idle",
            "total_posts": 0,
            "processed": 0,
            "remaining": 0,
            "successful": 0,
            "failed": 0,
            "started_at": None,
            "updated_at": None,
        }
        self._running_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self.settings = get_settings()
        self._processed_post_ids: set[str] = set()
        self._failed_post_ids: set[str] = set()
        self._initialized = True
        
    def _get_pending_count(self, db: Session) -> int:
        stmt = (
            select(func.count(Post.id))
            .select_from(Post)
            .outerjoin(Analysis, Analysis.post_id == Post.id)
            .where(Analysis.id.is_(None))
        )
        return db.execute(stmt).scalar() or 0
        
    def _fetch_batch(self, db: Session, batch_size: int) -> list[Post]:
        # Fetch posts not already in processed or failed sets
        subquery = select(Analysis.post_id).subquery()
        stmt = (
            select(Post)
            .where(Post.id.not_in(subquery))
            .where(Post.id.not_in(self._processed_post_ids))
            .where(Post.id.not_in(self._failed_post_ids))
            .order_by(Post.collected_at.desc())
            .limit(batch_size)
        )
        return list(db.scalars(stmt).all())
        
    def _process_single_post(self, post: Post) -> bool:
        db = SessionLocal()
        try:
            # Check if analysis already exists before processing
            existing_analysis = db.scalar(
                select(Analysis).where(Analysis.post_id == post.id)
            )
            if existing_analysis:
                logger.info("Skipping already analysed post_id=%s", post.id)
                return True
                
            analyzer = GroqAnalyzer(self.settings)
            text = self._build_input_text(post)
            result = analyzer.analyze(text)
            
            analysis = Analysis(
                post_id=post.id,
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
            logger.info(
                "Stored Groq analysis post_id=%s category=%s sentiment=%s language=%s",
                post.id,
                analysis.category,
                analysis.sentiment,
                analysis.language,
            )
            return True
        except Exception as e:
            logger.exception(
                "Failed to analyse post_id=%s platform=%s platform_post_id=%s",
                post.id,
                post.platform,
                post.platform_post_id,
            )
            db.rollback()
            return False
        finally:
            db.close()
            
    def _process_all(self):
        self.status["status"] = "running"
        self.status["started_at"] = datetime.now(timezone.utc).isoformat()
        self.status["processed"] = 0
        self.status["successful"] = 0
        self.status["failed"] = 0
        self._processed_post_ids = set()
        self._failed_post_ids = set()
        self._stop_event.clear()
        
        batch_size = self.settings.analysis_batch_size
        max_workers = 5
        
        while not self._stop_event.is_set():
            db = SessionLocal()
            try:
                # Recompute pending count from DB each batch
                pending = self._get_pending_count(db)
                self.status["total_posts"] = db.query(Post).count()
                self.status["remaining"] = pending
                self.status["updated_at"] = datetime.now(timezone.utc).isoformat()

                if pending == 0:
                    logger.info("No more posts to analyze!")
                    self.status["status"] = "completed"
                    self.status["updated_at"] = datetime.now(timezone.utc).isoformat()
                    break

                # Fetch a new batch
                batch = self._fetch_batch(db, batch_size)
                if not batch:
                    logger.info("No more posts to analyze!")
                    self.status["status"] = "completed"
                    self.status["updated_at"] = datetime.now(timezone.utc).isoformat()
                    break

                logger.info(
                    f"Batch fetched: {len(batch)}, "
                    f"Processed: {self.status['processed']}, "
                    f"Failed: {self.status['failed']}, "
                    f"Pending: {pending}"
                )
            finally:
                db.close()

            # Process the batch
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_post = {
                    executor.submit(self._process_single_post, post): post
                    for post in batch
                }

                for future in as_completed(future_to_post):
                    if self._stop_event.is_set():
                        break

                    post = future_to_post[future]
                    try:
                        success = future.result()
                        self._processed_post_ids.add(post.id)
                        self.status["processed"] += 1
                        if success:
                            self.status["successful"] += 1
                        else:
                            self._failed_post_ids.add(post.id)
                            self.status["failed"] += 1

                        self.status["updated_at"] = datetime.now(timezone.utc).isoformat()
                        logger.debug(
                            f"Progress: processed {self.status['processed']}, "
                            f"failed {self.status['failed']}, "
                            f"successful {self.status['successful']}"
                        )
                    except Exception as e:
                        logger.exception(f"Error processing post {post.id}")
                        self._processed_post_ids.add(post.id)
                        self._failed_post_ids.add(post.id)
                        self.status["processed"] += 1
                        self.status["failed"] += 1
                        self.status["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Final status update
        db = SessionLocal()
        try:
            final_pending = self._get_pending_count(db)
            self.status["remaining"] = final_pending
            if final_pending == 0:
                self.status["status"] = "completed"
            self.status["updated_at"] = datetime.now(timezone.utc).isoformat()
            logger.info(
                f"Analysis job finished: "
                f"status={self.status['status']}, "
                f"total_processed={self.status['processed']}, "
                f"successful={self.status['successful']}, "
                f"failed={self.status['failed']}, "
                f"remaining={final_pending}"
            )
        finally:
            db.close()
        
    def start_analysis(self) -> bool:
        with self._lock:
            if self.status["status"] == "running":
                logger.info("Analysis is already running!")
                return False
                
            self._running_thread = threading.Thread(
                target=self._process_all,
                daemon=True,
            )
            self._running_thread.start()
            logger.info("Started analysis background job")
            return True
            
    def get_status(self) -> Dict[str, Any]:
        return self.status.copy()
        
    def stop_analysis(self):
        self._stop_event.set()
        if self._running_thread and self._running_thread.is_alive():
            self._running_thread.join(timeout=5)
        
    @staticmethod
    def _build_input_text(post: Post) -> str:
        parts = [post.title or "", post.content or ""]
        return "\n\n".join(part for part in parts if part.strip())

