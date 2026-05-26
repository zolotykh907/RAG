import os
from typing import Any, Optional, Tuple

import numpy as np

from rag_system.shared.logs import setup_logging


class FaissDB:
    """Manage FAISS index creation, persistence, loading, and search."""

    def __init__(self, config: Any, k: int = 5) -> None:
        self.index_path: str = config.index_path
        self.logs_dir: str = config.logs_dir
        self.index: Optional[Any] = None
        self.k: int = k
        self.hnsw_m: int = int(getattr(config, 'hnsw_m', 32))
        self.hnsw_ef_construction: int = int(getattr(config, 'hnsw_ef_construction', 200))
        self.hnsw_ef_search: int = int(getattr(config, 'hnsw_ef_search', 64))
        self.logger = setup_logging(self.logs_dir, 'FaissDB')

    def create_index(self, embeddings: np.ndarray, replace: bool = False) -> None:
        """Create a new FAISS index or update an existing one.

        Args:
            embeddings: L2-normalized numpy array of embeddings to index.
            replace: If True, replace the existing index instead of adding to it.

        Raises:
            Exception: If FAISS cannot build, update, or persist the index.
        """
        try:
            if self.index is None or replace:
                if replace and self.index is not None:
                    self.logger.info("Replacing existing FAISS index.")

                self.index = self.build_index(embeddings, add_embeddings=False)
                self.logger.info(
                    f"Created FAISS HNSW index: dim={embeddings.shape[1]}, M={self.hnsw_m}, "
                    f"efConstruction={self.hnsw_ef_construction}."
                )

            assert self.index is not None
            self.index.add(np.array(embeddings, dtype=np.float32))
            import faiss

            faiss.write_index(self.index, self.index_path)
            self.logger.info(f"FAISS index saved to {self.index_path}.")
        except Exception as e:
            self.logger.error(f'Error adding embeddings or creating index: {e}')
            raise

    def build_index(self, embeddings: np.ndarray, add_embeddings: bool = True) -> Any:
        """Build a FAISS HNSW index in memory.

        Args:
            embeddings: Embedding matrix used to infer index dimensionality.
            add_embeddings: If True, add the provided embeddings to the index.

        Returns:
            A FAISS index instance.
        """
        import faiss

        dim = embeddings.shape[1]
        index = faiss.IndexHNSWFlat(dim, self.hnsw_m, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = self.hnsw_ef_construction
        if add_embeddings:
            index.add(np.array(embeddings, dtype=np.float32))
        return index

    def load_index(self, index_path: Optional[str] = None) -> None:
        """Load the FAISS index from file.

        Args:
            index_path: Optional path to the index file.
        """
        if index_path is None:
            index_path = self.index_path
        if not os.path.exists(index_path):
            self.logger.info(f"Index file not found at {index_path}")
            self.index = None
            return
        try:
            import faiss

            self.index = faiss.read_index(index_path)
            self.logger.info(f'Index loaded from {index_path}')
        except Exception as e:
            self.logger.error(f"Failed to load FAISS index from {index_path}: {str(e)}")
            self.index = None

    def search(self, request_embedding: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Nearest-neighbor search in FAISS.

        Args:
            request_embedding: L2-normalized query embedding vector.
            k: Number of nearest neighbors to return.

        Returns:
            Tuple of (indices, scores) arrays for the k nearest neighbors.
            Scores are cosine similarities (higher = more similar).
        """
        if self.index is None:
            self.logger.warning("Index is not loaded or created. Returning empty result.")
            return np.array([]), np.array([])

        if self.index.ntotal == 0:
            self.logger.warning("Index is empty. Returning empty result.")
            return np.array([]), np.array([])

        actual_k = min(k, self.index.ntotal)

        if hasattr(self.index, 'hnsw'):
            self.index.hnsw.efSearch = self.hnsw_ef_search

        scores, ids = self.index.search(request_embedding, actual_k)

        valid_mask = ids[0] != -1
        valid_ids = ids[0][valid_mask]
        valid_scores = scores[0][valid_mask]

        self.logger.debug(f"Search returned {len(valid_ids)} valid results out of {actual_k} requested")
        return valid_ids, valid_scores

    def delete_index(self) -> None:
        """Delete the persisted FAISS index and reset the in-memory index."""
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
            self.logger.info(f'Deleted index at {self.index_path}')
        self.index = None

    def clear_index(self) -> None:
        """Clear the FAISS index using the deletion workflow."""
        self.delete_index()
