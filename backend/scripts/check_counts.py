import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.post import Post
from app.models.analysis import Analysis
from app.models.cluster import Cluster
from app.models.cluster_membership import ClusterMembership


def main():
    db = SessionLocal()
    try:
        post_count = db.query(Post).count()
        analysis_count = db.query(Analysis).count()
        analysis_with_embedding = db.query(Analysis).filter(Analysis.embedding.isnot(None)).count()
        cluster_count = db.query(Cluster).count()
        membership_count = db.query(ClusterMembership).count()

        print("Current Database Counts:")
        print(f"  Posts: {post_count}")
        print(f"  Analysis Records: {analysis_count}")
        print(f"  Analysis with Embeddings: {analysis_with_embedding}")
        print(f"  Clusters: {cluster_count}")
        print(f"  Cluster Memberships: {membership_count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
