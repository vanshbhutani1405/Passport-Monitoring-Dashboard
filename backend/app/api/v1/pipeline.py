import logging
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analysis_service import AnalysisService
from app.services.clustering_service import ClusteringService
from app.services.embedding_pipeline import EmbeddingPipeline
from app.services.google_news_ingestion import GoogleNewsIngestionService
from app.services.youtube_ingestion import YouTubeIngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/ingest")
async def ingest_data(db: Session = Depends(get_db)) -> Dict:
    logger.info("Starting manual ingestion pipeline")
    status = {
        "google_news": "running",
        "youtube": "pending",
        "success": False
    }

    try:
        google_news_service = GoogleNewsIngestionService()
        google_news_run = google_news_service.ingest()
        status["google_news"] = "success"
        logger.info("Google News ingestion complete: found=%s saved=%s", google_news_run.posts_found, google_news_run.posts_saved)

        status["youtube"] = "running"
        youtube_service = YouTubeIngestionService()
        youtube_run = youtube_service.ingest()
        status["youtube"] = "success"
        logger.info("YouTube ingestion complete: found=%s saved=%s", youtube_run.posts_found, youtube_run.posts_saved)

        status["success"] = True
        return status
    except Exception as e:
        logger.exception("Ingestion pipeline failed")
        status["success"] = False
        status["error"] = str(e)
        if status["google_news"] == "running":
            status["google_news"] = "failed"
        elif status["youtube"] == "running":
            status["youtube"] = "failed"
        return status


@router.post("/analyze")
async def analyze_data(db: Session = Depends(get_db)) -> Dict:
    logger.info("Starting analysis pipeline")
    status = {
        "analysis": "running",
        "success": False
    }

    try:
        analysis_service = AnalysisService(db)
        result = analysis_service.process_unanalysed_posts()
        status["analysis"] = "success"
        status["found"] = result["found"]
        status["processed"] = result["processed"]
        status["failed"] = result["failed"]
        status["success"] = True
        logger.info("Analysis complete: found=%s processed=%s failed=%s", result["found"], result["processed"], result["failed"])
        return status
    except Exception as e:
        logger.exception("Analysis pipeline failed")
        status["analysis"] = "failed"
        status["success"] = False
        status["error"] = str(e)
        return status


@router.post("/embed")
async def generate_embeddings(db: Session = Depends(get_db)) -> Dict:
    logger.info("Starting embedding pipeline")
    status = {
        "embeddings": "running",
        "success": False
    }

    try:
        embedding_pipeline = EmbeddingPipeline(db)
        result = embedding_pipeline.process_missing_embeddings()
        status["embeddings"] = "success"
        status["found"] = result["found"]
        status["processed"] = result["processed"]
        status["failed"] = result["failed"]
        status["success"] = True
        logger.info("Embeddings complete: found=%s processed=%s failed=%s", result["found"], result["processed"], result["failed"])
        return status
    except Exception as e:
        logger.exception("Embedding pipeline failed")
        status["embeddings"] = "failed"
        status["success"] = False
        status["error"] = str(e)
        return status


@router.post("/cluster")
async def cluster_data(db: Session = Depends(get_db)) -> Dict:
    logger.info("Starting clustering pipeline")
    status = {
        "clustering": "running",
        "success": False
    }

    try:
        clustering_service = ClusteringService(db)
        result = clustering_service.rebuild_clusters()
        status["clustering"] = "success"
        status["eligible_posts"] = result.get("eligible_posts", 0)
        status["cluster_count"] = result.get("cluster_count", 0)
        status["cluster_memberships"] = result.get("cluster_memberships", 0)
        status["success"] = True
        logger.info("Clustering complete: eligible_posts=%s clusters=%s memberships=%s", result.get("eligible_posts", 0), result.get("cluster_count", 0), result.get("cluster_memberships", 0))
        return status
    except Exception as e:
        logger.exception("Clustering pipeline failed")
        status["clustering"] = "failed"
        status["success"] = False
        status["error"] = str(e)
        return status


@router.post("/run-all")
async def run_full_pipeline(db: Session = Depends(get_db)) -> Dict:
    logger.info("Starting full pipeline execution")
    status = {
        "ingestion": "pending",
        "analysis": "pending",
        "embeddings": "pending",
        "clustering": "pending",
        "success": False
    }

    try:
        # Ingestion
        status["ingestion"] = "running"
        google_news_service = GoogleNewsIngestionService()
        google_news_service.ingest()
        youtube_service = YouTubeIngestionService()
        youtube_service.ingest()
        status["ingestion"] = "success"

        # Analysis
        status["analysis"] = "running"
        analysis_service = AnalysisService(db)
        analysis_service.process_unanalysed_posts()
        status["analysis"] = "success"

        # Embeddings
        status["embeddings"] = "running"
        embedding_pipeline = EmbeddingPipeline(db)
        embedding_pipeline.process_missing_embeddings()
        status["embeddings"] = "success"

        # Clustering
        status["clustering"] = "running"
        clustering_service = ClusteringService(db)
        clustering_service.rebuild_clusters()
        status["clustering"] = "success"

        status["success"] = True
        logger.info("Full pipeline execution complete")
        return status
    except Exception as e:
        logger.exception("Full pipeline execution failed")
        status["success"] = False
        status["error"] = str(e)
        if status["ingestion"] == "running":
            status["ingestion"] = "failed"
        elif status["analysis"] == "running":
            status["analysis"] = "failed"
        elif status["embeddings"] == "running":
            status["embeddings"] = "failed"
        elif status["clustering"] == "running":
            status["clustering"] = "failed"
        return status
