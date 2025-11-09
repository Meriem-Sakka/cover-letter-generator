"""
Vector store wrapper with FAISS fallback to NumPy.
Provides simple index->add->search API for dense vectors.
"""

from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, dim: int, use_faiss: bool = True, metric: str = "ip"):
        """
        Args:
            dim: vector dimensionality
            use_faiss: try to use FAISS if available
            metric: 'ip' (inner product) or 'l2'
        """
        self.dim = dim
        self.metric = metric
        self._use_faiss = False
        self._ids: List[int] = []
        self._data: List[List[float]] = []
        self._index = None

        if use_faiss:
            try:
                import faiss  # type: ignore
                self.faiss = faiss
                if metric == "l2":
                    self._index = faiss.IndexFlatL2(dim)
                else:
                    self._index = faiss.IndexFlatIP(dim)
                self._use_faiss = True
                logger.info("FAISS vector index initialized")
            except Exception as e:
                logger.warning(f"FAISS not available ({e}); using NumPy fallback")
                self.faiss = None

    def add(self, vectors: List[List[float]], ids: Optional[List[int]] = None) -> None:
        if not vectors:
            return
        if ids is None:
            start = len(self._ids)
            ids = list(range(start, start + len(vectors)))
        if self._use_faiss:
            import numpy as np
            arr = np.array(vectors, dtype="float32")
            if self.metric == "ip":
                # normalize for cosine
                norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9
                arr = arr / norms
            self._index.add(arr)
            self._ids.extend(ids)
        else:
            self._ids.extend(ids)
            self._data.extend(vectors)

    def search(self, query_vectors: List[List[float]], top_k: int = 5) -> List[List[Tuple[int, float]]]:
        """
        Returns top_k results per query as list of (id, score) pairs per query.
        """
        if not query_vectors:
            return []

        if self._use_faiss:
            import numpy as np
            q = np.array(query_vectors, dtype="float32")
            if self.metric == "ip":
                norms = np.linalg.norm(q, axis=1, keepdims=True) + 1e-9
                q = q / norms
            D, I = self._index.search(q, top_k)
            results: List[List[Tuple[int, float]]] = []
            for row_i, row_d in zip(I, D):
                row: List[Tuple[int, float]] = []
                for idx, dist in zip(row_i, row_d):
                    if idx == -1:
                        continue
                    stored_id = self._ids[idx] if idx < len(self._ids) else idx
                    score = float(dist) if self.metric == "ip" else float(-dist)
                    row.append((stored_id, score))
                results.append(row)
            return results

        # NumPy fallback (cosine)
        try:
            import numpy as np
            data = np.array(self._data, dtype="float32")
            q = np.array(query_vectors, dtype="float32")
            if data.size == 0:
                return [[] for _ in query_vectors]
            data_norm = data / (np.linalg.norm(data, axis=1, keepdims=True) + 1e-9)
            q_norm = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-9)
            sims = q_norm @ data_norm.T
            results: List[List[Tuple[int, float]]] = []
            for row in sims:
                top_idx = row.argsort()[::-1][:top_k]
                results.append([(self._ids[i], float(row[i])) for i in top_idx])
            return results
        except Exception:
            return [[] for _ in query_vectors]


