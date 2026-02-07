import os

import faiss
import numpy as np

from app.shared.logs import setup_logging


class FaissDB:
    def __init__(self, config, k=5):
        self.index_path = config.index_path
        self.logs_dir = config.logs_dir
        self.index = None
        self.k = k
        self.logger = setup_logging(self.logs_dir, 'FaissDB')

    def create_index(self, embeddings, replace=False):
        """Create a new FAISS index or updates an existing.

        Args:
            embeddings (np.ndarray): numpy array of embeddings to index
            replace (bool): if True, replace existing index instead of adding to it
        """
        try:
            if self.index is None or replace:
                if replace and self.index is not None:
                    self.logger.info("Replacing existing FAISS index.")

                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dim)
                self.logger.info(f"Created new FAISS index with dimension {dim}.")

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
            request_embedding (np.ndarray): Query embedding vector.
            k (int): Number of nearest neighbors to return.

        Returns:
            np.ndarray: array of indices of the k nearest neighbors.
        """
        if self.index is None:
            self.logger.warning("Index is not loaded or created. Returning empty result.")
            return np.array([])

        if self.index.ntotal == 0:
            self.logger.warning("Index is empty. Returning empty result.")
            return np.array([])

        actual_k = min(k, self.index.ntotal)

        d, ids = self.index.search(request_embedding, actual_k)

        valid_ids = ids[0][ids[0] != -1]

        self.logger.debug(f"Search returned {len(valid_ids)} valid results out of {actual_k} requested")
        return valid_ids

    def delete_index(self):
        """Deletes the FAISS index."""
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
            self.index = None
            self.logger.info(f'Deleted index at {self.index_path}')

    def clear_index(self):
        """Clears the FAISS index (alias for delete_index)."""
        self.delete_index()
