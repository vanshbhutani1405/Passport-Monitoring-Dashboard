import logging
from collections import Counter, defaultdict
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.cluster import Cluster
from app.models.cluster_membership import ClusterMembership
from app.models.post import Post
from app.nlp.clustering import ClusterAssignment, ClusteringEngine


logger = logging.getLogger(__name__)


CATEGORY_TITLES = {
    "passport_renewal": "Passport Renewal Discussions",
    "passport_delay": "Passport Delay Reports",
    "passport_application": "Passport Application Questions",
    "passport_appointment": "Appointment Scheduling Issues",
    "passport_verification": "Passport Verification Concerns",
    "passport_status": "Passport Status Tracking Problems",
    "passport_lost": "Lost Passport Issues",
    "passport_general": "General Passport Discussions",
    "other": "Other Passport Discussions",
}


@dataclass(frozen=True)
class ClusterInput:
    post: Post
    analysis: Analysis


class ClusteringService:
    def __init__(
        self,
        db: Session,
        clustering_engine: ClusteringEngine | None = None,
    ) -> None:
        self.db = db
        self.clustering_engine = clustering_engine or ClusteringEngine()

    def rebuild_clusters(self, limit: int | None = None) -> dict[str, int]:
        inputs = self._fetch_cluster_inputs(limit=limit)
        stats = {
            "eligible_posts": len(inputs),
            "clusters_created": 0,
            "memberships_created": 0,
        }

        if not inputs:
            logger.info("No embedded analyses found for clustering")
            self._clear_existing_clusters()
            self.db.commit()
            return stats

        logger.info("Starting semantic clustering: eligible_posts=%s limit=%s", len(inputs), limit)

        try:
            embeddings_list = []
            for item in inputs:
                if item.analysis.embedding is not None:
                    embeddings_list.append(list(item.analysis.embedding))
                else:
                    embeddings_list.append([])
            assignments = self.clustering_engine.cluster(embeddings_list)
            grouped_assignments = self._group_assignments(assignments)

            self._clear_existing_clusters()

            for cluster_label, cluster_assignments in grouped_assignments.items():
                cluster = self._create_cluster(
                    inputs=inputs,
                    assignments=cluster_assignments,
                    cluster_label=cluster_label,
                )
                self.db.add(cluster)
                self.db.flush()

                for assignment in cluster_assignments:
                    item = inputs[assignment.item_index]
                    self.db.add(
                        ClusterMembership(
                            cluster_id=cluster.id,
                            post_id=item.post.id,
                            similarity_score=assignment.similarity_score,
                        )
                    )

                stats["clusters_created"] += 1
                stats["memberships_created"] += len(cluster_assignments)

            self.db.commit()
            logger.info(
                "Semantic clustering completed: eligible_posts=%s clusters=%s memberships=%s",
                stats["eligible_posts"],
                stats["clusters_created"],
                stats["memberships_created"],
            )
            return {
                "eligible_posts": stats["eligible_posts"],
                "cluster_count": stats["clusters_created"],
                "cluster_memberships": stats["memberships_created"],
            }

        except Exception:
            logger.exception("Semantic clustering failed")
            self.db.rollback()
            raise

    def _fetch_cluster_inputs(self, limit: int | None) -> list[ClusterInput]:
        statement = (
            select(Post, Analysis)
            .join(Analysis, Analysis.post_id == Post.id)
            .where(
                Analysis.embedding.is_not(None),
                Analysis.is_duplicate.is_(False),
            )
            .order_by(Post.collected_at.asc())
        )
        if limit is not None:
            statement = statement.limit(limit)

        try:
            rows = self.db.execute(statement).all()
        except SQLAlchemyError:
            logger.exception("Failed to fetch embedded analyses for clustering")
            raise

        return [ClusterInput(post=post, analysis=analysis) for post, analysis in rows]

    def _clear_existing_clusters(self) -> None:
        self.db.execute(delete(ClusterMembership))
        self.db.execute(delete(Cluster))

    @staticmethod
    def _group_assignments(
        assignments: list[ClusterAssignment],
    ) -> dict[int, list[ClusterAssignment]]:
        grouped: dict[int, list[ClusterAssignment]] = defaultdict(list)
        for assignment in assignments:
            grouped[assignment.cluster_label].append(assignment)
        return dict(grouped)

    def _create_cluster(
        self,
        inputs: list[ClusterInput],
        assignments: list[ClusterAssignment],
        cluster_label: int,
    ) -> Cluster:
        analyses = [inputs[assignment.item_index].analysis for assignment in assignments]
        dominant_category = self._most_common([analysis.category for analysis in analyses])
        dominant_sentiment = self._most_common([analysis.sentiment for analysis in analyses])
        name = self._generate_cluster_title(dominant_category=dominant_category, analyses=analyses)
        description = self._generate_cluster_description(
            name=name,
            dominant_sentiment=dominant_sentiment,
            post_count=len(assignments),
            cluster_label=cluster_label,
        )

        return Cluster(
            name=name,
            description=description,
            dominant_category=dominant_category,
            dominant_sentiment=dominant_sentiment,
            post_count=len(assignments),
        )

    @staticmethod
    def _most_common(values: list[str]) -> str | None:
        if not values:
            return None
        return Counter(values).most_common(1)[0][0]

    @staticmethod
    def _generate_cluster_title(dominant_category: str | None, analyses: list[Analysis]) -> str:
        if dominant_category in CATEGORY_TITLES:
            return CATEGORY_TITLES[dominant_category]

        summaries = [analysis.summary for analysis in analyses if analysis.summary]
        if summaries:
            first_summary = summaries[0].strip().rstrip(".")
            return first_summary[:120]

        return "Passport Discussion Cluster"

    @staticmethod
    def _generate_cluster_description(
        name: str,
        dominant_sentiment: str | None,
        post_count: int,
        cluster_label: int,
    ) -> str:
        sentiment_text = dominant_sentiment or "unknown"
        return (
            f"{name} grouped from {post_count} semantically similar posts. "
            f"Dominant sentiment: {sentiment_text}. Cluster label: {cluster_label}."
        )
