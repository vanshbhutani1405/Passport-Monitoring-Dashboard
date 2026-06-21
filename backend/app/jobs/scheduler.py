import logging
from threading import Lock

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.services.analysis_service import AnalysisService
from app.services.clustering_service import ClusteringService
from app.services.embedding_pipeline import EmbeddingPipeline
from app.services.google_news_ingestion import GoogleNewsIngestionService
from app.services.youtube_ingestion import YouTubeIngestionService


logger = logging.getLogger(__name__)


class PipelineScheduler:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._scheduler = None
        self._pipeline_lock = Lock()

    def start(self) -> None:
        if self._scheduler:
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError as exc:
            raise RuntimeError("APScheduler is required for scheduled ingestion.") from exc

        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._scheduler.add_job(
            self.run_pipeline,
            "interval",
            minutes=self.settings.pipeline_interval_minutes,
            id="passport_monitor_pipeline",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()
        logger.info(
            "Pipeline scheduler started interval_minutes=%s",
            self.settings.pipeline_interval_minutes,
        )

    def shutdown(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("Pipeline scheduler stopped")

    def run_pipeline(self) -> dict[str, object]:
        if not self._pipeline_lock.acquire(blocking=False):
            logger.info("Skipping pipeline run because a previous run is still active")
            return {"status": "skipped", "reason": "already_running"}

        results: dict[str, object] = {"status": "completed"}
        try:
            logger.info("Starting scheduled MVP pipeline")
            results["google_news"] = self._run_stage("google_news_ingestion", self._run_google_news)
            results["youtube"] = self._run_stage("youtube_ingestion", self._run_youtube)
            results["analysis"] = self._run_stage("groq_analysis", self._run_analysis)
            results["embeddings"] = self._run_stage("embeddings", self._run_embeddings)
            results["clustering"] = self._run_stage("clustering", self._run_clustering)
            logger.info("Scheduled MVP pipeline completed results=%s", results)
            return results
        finally:
            self._pipeline_lock.release()

    def _run_stage(self, stage_name: str, stage_callable):
        try:
            logger.info("Pipeline stage started stage=%s", stage_name)
            result = stage_callable()
            logger.info("Pipeline stage completed stage=%s result=%s", stage_name, result)
            return {"status": "success", "result": result}
        except Exception as exc:
            logger.exception("Pipeline stage failed stage=%s", stage_name)
            return {"status": "failed", "error": str(exc)}

    def _run_google_news(self) -> dict[str, object]:
        run = GoogleNewsIngestionService().ingest()
        return {"run_id": str(run.id), "status": run.status, "posts_saved": run.posts_saved}

    def _run_youtube(self) -> dict[str, object]:
        run = YouTubeIngestionService().ingest(
                max_results_per_keyword=self.settings.youtube_max_results_per_keyword
            )
        return {"run_id": str(run.id), "status": run.status, "posts_saved": run.posts_saved}

    def _run_analysis(self) -> dict[str, int]:
        with SessionLocal() as db:
            return AnalysisService(db).process_unanalysed_posts(limit=self.settings.analysis_batch_size)

    def _run_embeddings(self) -> dict[str, int]:
        with SessionLocal() as db:
            return EmbeddingPipeline(db).process_missing_embeddings(limit=self.settings.embedding_batch_size)

    def _run_clustering(self) -> dict[str, int]:
        with SessionLocal() as db:
            return ClusteringService(db).rebuild_clusters(limit=self.settings.clustering_limit)
