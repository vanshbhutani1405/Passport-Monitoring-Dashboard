import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.services.clustering_service import ClusteringService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    db = SessionLocal()
    try:
        logger.info("=== Running Clustering ===")
        clustering_service = ClusteringService(db)
        clustering_result = clustering_service.rebuild_clusters()
        print("\nClustering Result:")
        print(f"  Eligible posts: {clustering_result.get('eligible_posts', 0)}")
        print(f"  Clusters created: {clustering_result.get('cluster_count', 0)}")
        print(f"  Memberships created: {clustering_result.get('cluster_memberships', 0)}")
    except Exception as e:
        logger.exception("Clustering failed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
