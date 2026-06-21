import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.services.analysis_service import AnalysisService
from app.services.embedding_pipeline import EmbeddingPipeline
from app.services.clustering_service import ClusteringService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    db = SessionLocal()
    try:
        logger.info("=== Running Analysis Service ===")
        analysis_service = AnalysisService(db)
        analysis_result = analysis_service.process_unanalysed_posts()
        print("\nAnalysis Result:")
        print(f"  found: {analysis_result['found']}")
        print(f"  processed: {analysis_result['processed']}")
        print(f"  failed: {analysis_result['failed']}")

        logger.info("\n=== Running Embedding Pipeline ===")
        embedding_pipeline = EmbeddingPipeline(db)
        embedding_result = embedding_pipeline.process_missing_embeddings()
        print("\nEmbedding Result:")
        print(f"  found: {embedding_result['found']}")
        print(f"  processed: {embedding_result['processed']}")
        print(f"  failed: {embedding_result['failed']}")

        logger.info("\n=== Running Clustering Service ===")
        clustering_service = ClusteringService(db)
        clustering_result = clustering_service.rebuild_clusters()
        print("\nClustering Result:")
        print(f"  eligible_posts: {clustering_result.get('eligible_posts', 0)}")
        print(f"  clusters_created: {clustering_result.get('clusters_created', 0)}")
        print(f"  memberships_created: {clustering_result.get('memberships_created', 0)}")

    except Exception as e:
        logger.exception("Manual pipeline failed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
