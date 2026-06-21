import logging
from dataclasses import dataclass

import numpy as np


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClusterAssignment:
    item_index: int
    cluster_label: int
    similarity_score: float


class ClusteringEngine:
    def __init__(
        self,
        min_cluster_size: int = 3,
        min_samples: int = 2,
        similarity_threshold: float = 0.72,
    ) -> None:
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.similarity_threshold = similarity_threshold

    def cluster(self, embeddings: list[list[float]]) -> list[ClusterAssignment]:
        if len(embeddings) < self.min_cluster_size:
            logger.info(
                "Skipping clustering because embedding count=%s is below min_cluster_size=%s",
                len(embeddings),
                self.min_cluster_size,
            )
            return []

        matrix = self._normalize(np.array(embeddings, dtype=np.float32))
        distance_matrix = np.clip(1 - np.matmul(matrix, matrix.T), 0, 2)
        labels = self._fit_labels(distance_matrix)
        return self._build_assignments(matrix=matrix, labels=labels)

    def _fit_labels(self, distance_matrix: np.ndarray) -> np.ndarray:
        try:
            import hdbscan

            logger.info("Using HDBSCAN for semantic clustering")
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric="precomputed",
            )
            distance_matrix_f64 = distance_matrix.astype(np.float64)
            return clusterer.fit_predict(distance_matrix_f64)
        except ImportError:
            logger.info("HDBSCAN not installed; falling back to DBSCAN")

        try:
            from sklearn.cluster import DBSCAN
        except ImportError as exc:
            raise RuntimeError("Either hdbscan or scikit-learn is required for clustering.") from exc

        clusterer = DBSCAN(
            eps=1 - self.similarity_threshold,
            min_samples=self.min_samples,
            metric="precomputed",
        )
        return clusterer.fit_predict(distance_matrix)

    @staticmethod
    def _normalize(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return matrix / norms

    @staticmethod
    def _build_assignments(matrix: np.ndarray, labels: np.ndarray) -> list[ClusterAssignment]:
        assignments: list[ClusterAssignment] = []

        for label in sorted(set(labels)):
            if label == -1:
                continue

            member_indices = np.where(labels == label)[0]
            centroid = matrix[member_indices].mean(axis=0)
            centroid = centroid / (np.linalg.norm(centroid) or 1)

            for item_index in member_indices:
                similarity = float(np.dot(matrix[item_index], centroid))
                assignments.append(
                    ClusterAssignment(
                        item_index=int(item_index),
                        cluster_label=int(label),
                        similarity_score=round(similarity, 4),
                    )
                )

        return assignments
