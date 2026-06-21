import logging
from threading import Lock


logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


class EmbeddingService:
    _model = None
    _model_lock = Lock()

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        self.model_name = model_name

    def _get_model(self):
        if EmbeddingService._model is not None:
            return EmbeddingService._model

        with EmbeddingService._model_lock:
            if EmbeddingService._model is not None:
                return EmbeddingService._model

            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is required for embedding generation."
                ) from exc

            logger.info("Loading sentence transformer model=%s", self.model_name)
            EmbeddingService._model = SentenceTransformer(self.model_name)
            return EmbeddingService._model

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []

        model = self._get_model()
        cleaned_texts = [self._clean_text(text) for text in texts]

        embeddings = model.encode(
            cleaned_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return [embedding.astype(float).tolist() for embedding in embeddings]

    @staticmethod
    def _clean_text(text: str) -> str:
        normalized = " ".join((text or "").split())
        return normalized[:8000] or "empty content"
