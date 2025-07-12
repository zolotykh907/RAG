import os
import faiss
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logs import setup_logging 


class FaissDB:
    def __init__(self, config, k=5):
        self.index_path = config.index_path
        self.logs_dir = config.logs_dir
        self.index = None
        self.k = k
        self.logger = setup_logging(self.logs_dir, 'FaissDB')


    def create_index(self, embeddings):
        """Create a new FAISS index or updates an existing.

        Args:
            embeddings (np.ndarray): numpy array of embeddings to index
        """
        try:
            if self.index is None:
                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dim)
                self.logger.info(f"Created new FAISS index with dimension {dim}.")

            self.index.add(np.array(embeddings, dtype=np.float32))
            faiss.write_index(self.index, self.index_path)
            self.logger.info(f"FAISS index saved to {self.index_path}.")
        except Exception as e:
            self.logger.info(f'Error added embeddings or create index: {e}')
            raise

    def load_index(self, index_path=None):
        """Load the FAISS index and processed text data from files."""
        if index_path is None:
            index_path = self.index_path
        if not os.path.exists(self.index_path):
            self.logger.info(f"Index file not found at {self.index_path}")
        try:
            self.index = faiss.read_index(self.index_path)
            self.logger.info(f'Index loaded from {self.index_path}')
        except Exception as e:
            self.logger.error(f"Failed to load FAISS index from {self.index_path}: {str(e)}")
            raise

    
    def search(self, request_embedding):
        """Nearest-neighbor search in FAISS.

        Args:
            request_embedding (np.ndarray): Query embedding vector. 

        Returns:
            np.ndarray: array of indices of the k nearest neighbors.
        """
        if self.index is None:
            raise RuntimeError("Index is not loaded or created")
        
        d, ids = self.index.search(request_embedding, self.k)
        return ids[0]
    

    def delete_index(self):
        """Deletes the FAISS index."""
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
            self.index = None
            self.logger.info(f'Deleted index at {self.index_path}')
    

