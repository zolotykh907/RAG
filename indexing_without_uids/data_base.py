import os
import faiss
import numpy as np

try:
    from logs import setup_logging  
except ImportError:
    from ..indexing.logs import setup_logging 


class FaissDB:
    def __init__(self, config, k=5):
        self.index_path = config.index_path
        self.logs_dir = config.logs_dir
        self.index = None
        self.k = k
        self.logger = setup_logging(self.logs_dir, 'FaissDB')


    def check_existing_index(self):
        """"Load existing index FAISS."""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self.logger.info(f"Loaded existing index from {self.index_path}.")


    def create_index(self, embeddings):
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


    def load_index(self):
        """Load the FAISS index and processed text data from files."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"Index file not found at {self.index_path}")
        
        try:
            self.index = faiss.read_index(self.index_path)
            self.logger.info(f'Index loaded from {self.index_path}')
        except Exception as e:
            self.logger.error(f"Failed to load FAISS index from {self.index_path}: {str(e)}")
            raise

    
    def search(self, request_embedding):
        d, ids = self.index.search(request_embedding, self.k)

        return ids[0]
    

