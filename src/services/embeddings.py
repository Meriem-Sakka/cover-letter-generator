"""
Embeddings backend abstraction.
Supports Gemini (existing) and SentenceTransformers (optional).
Falls back gracefully if optional deps are unavailable.
"""

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class EmbeddingsBackend:
    """Abstract embeddings backend."""
    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class GeminiEmbeddingsBackend(EmbeddingsBackend):
    """Wrap existing GeminiService embedding API."""
    def __init__(self, gemini_service, mode: str = 'Fast', language: str = 'en'):
        self.gemini_service = gemini_service
        self.mode = mode
        self.language = language

    def embed(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for t in texts:
            try:
                if not t:
                    out.append([])
                    continue
                from src.utils.normalization import preprocess_for_embedding
                proc = preprocess_for_embedding(t, self.language)
                emb = self.gemini_service.get_embedding(proc, self.mode)
                out.append(emb or [])
            except Exception as e:
                logger.debug(f"Gemini embedding failed: {e}")
                out.append([])
        return out


class SBERTEmbeddingsBackend(EmbeddingsBackend):
    """SentenceTransformers backend (optional dependency)."""
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded SBERT model: {model_name}")
        except Exception as e:
            logger.warning(f"SBERT backend unavailable ({e}); falling back when used")

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not self.model:
            return [[] for _ in texts]
        try:
            vecs = self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            return [v.tolist() for v in vecs]
        except Exception as e:
            logger.debug(f"SBERT embedding failed: {e}")
            return [[] for _ in texts]


def build_embeddings_backend(
    backend: str,
    gemini_service=None,
    mode: str = 'Fast',
    language: str = 'en',
    sbert_model: Optional[str] = None
) -> EmbeddingsBackend:
    """
    Factory to construct an embeddings backend by name.
    backend: 'gemini' | 'sbert'
    """
    backend = (backend or 'gemini').lower()
    if backend == 'sbert':
        return SBERTEmbeddingsBackend(model_name=sbert_model or "sentence-transformers/all-MiniLM-L6-v2")
    return GeminiEmbeddingsBackend(gemini_service, mode, language)


