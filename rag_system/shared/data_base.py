import os

import faiss
import numpy as np

from rag_system.shared.logs import setup_logging


class FaissDB:
    def __init__(self, config, k=5):
        self.index_path = config.index_path
        self.logs_dir = config.logs_dir
        self.index = None
        self.k = k
        self.hnsw_m = int(getattr(config, 'hnsw_m', 32))
        self.hnsw_ef_construction = int(getattr(config, 'hnsw_ef_construction', 200))
        self.hnsw_ef_search = int(getattr(config, 'hnsw_ef_search', 64))
        self.logger = setup_logging(self.logs_dir, 'FaissDB')

    def create_index(self, embeddings, replace=False):
        """Create a new FAISS index or updates an existing.

        Args:
            embeddings (np.ndarray): L2-normalized numpy array of embeddings to index.
            replace (bool): if True, replace existing index instead of adding to it
        """
        try:
            if self.index is None or replace:
                if replace and self.index is not None:
                    self.logger.info("Replacing existing FAISS index.")

                dim = embeddings.shape[1]
                self.index = faiss.IndexHNSWFlat(dim, self.hnsw_m, faiss.METRIC_INNER_PRODUCT)
                self.index.hnsw.efConstruction = self.hnsw_ef_construction
                self.logger.info(
                    f"Created FAISS HNSW index: dim={dim}, M={self.hnsw_m}, "
                    f"efConstruction={self.hnsw_ef_construction}."
                )

            self.index.add(np.array(embeddings, dtype=np.float32))
            faiss.write_index(self.index, self.index_path)
            self.logger.info(f"FAISS index saved to {self.index_path}.")
        except Exception as e:
            self.logger.error(f'Error adding embeddings or creating index: {e}')
            raise

    def load_index(self, index_path=None):
        """Load the FAISS index from file.

        Args:
            index_path (str, optional): Path to the index file. Defaults to self.index_path.
        """
        if index_path is None:
            index_path = self.index_path
        if not os.path.exists(index_path):
            self.logger.info(f"Index file not found at {index_path}")
            self.index = None
            return
        try:
            self.index = faiss.read_index(index_path)
            self.logger.info(f'Index loaded from {index_path}')
        except Exception as e:
            self.logger.error(f"Failed to load FAISS index from {index_path}: {str(e)}")
            self.index = None

    def search(self, request_embedding, k):
        """Nearest-neighbor search in FAISS.

        Args:
            request_embedding (np.ndarray): L2-normalized query embedding vector.
            k (int): Number of nearest neighbors to return.

        Returns:
            tuple[np.ndarray, np.ndarray]: (indices, scores) of the k nearest neighbors.
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

    def delete_index(self):
        """Deletes the FAISS index."""
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
            self.index = None
            self.logger.info(f'Deleted index at {self.index_path}')

    def clear_index(self):
        """Clears the FAISS index (alias for delete_index)."""
        self.delete_index()
