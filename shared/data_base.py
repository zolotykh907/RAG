import os
import faiss
import numpy as np
#import chromadb
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
            self.index = None
            return
        try:
            self.index = faiss.read_index(self.index_path)
            self.logger.info(f'Index loaded from {self.index_path}')
        except Exception as e:
            self.logger.error(f"Failed to load FAISS index from {self.index_path}: {str(e)}")
            self.index = None

    
    def search(self, request_embedding, k):
        """Nearest-neighbor search in FAISS.

        Args:
            request_embedding (np.ndarray): Query embedding vector. 

        Returns:
            np.ndarray: array of indices of the k nearest neighbors.
        """
        if self.index is None:
            self.logger.warning("Index is not loaded or created. Returning empty result.")
            return np.array([])
        
        d, ids = self.index.search(request_embedding, k)
        return ids[0]
    

    def delete_index(self):
        """Deletes the FAISS index."""
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
            self.index = None
            self.logger.info(f'Deleted index at {self.index_path}')


class ChromaDB:
    """Chroma-based vector database implementation."""
    def __init__(self, config, k=5):
        self.index_path = config.index_path
        self.collection_name = 'ChromaDB'
        self.logs_dir = config.logs_dir
    #     self.k = k
    #     self.logger = setup_logging(self.logs_dir, 'ChromaDB')
    #     self.client = chromadb.PersistentClient(path=self.index_path)
    #     self.collection = None


    # def create_index(self, embeddings):
    #     """Create or update the Chroma collection with embeddings.

    #     Args:
    #         embeddings (np.ndarray): Numpy array of embeddings to index.
    #     """
    #     try:
    #         if self.collection is None:
    #             self.collection = self.client.create_collection(
    #                 name=self.collection_name,
    #                 metadata={"hnsw:space": "l2"}
    #             )
    #             self.logger.info(f"Created new Chroma collection: {self.collection_name}")
            
    #         # Convert embeddings to list and generate IDs
    #         embedding_list = embeddings.tolist()
    #         ids = [str(i) for i in range(len(embeddings))]
            
    #         self.collection.add(
    #             embeddings=embedding_list,
    #             ids=ids
    #         )
    #         self.logger.info(f"Added {len(embedding_list)} embeddings to Chroma collection {self.collection_name}")
    #         self.logger.info(f"ChromaDB index saved to {self.index_path}")
    #     except Exception as e:
    #         self.logger.error(f"Error creating or updating Chroma collection: {str(e)}")
    #         raise


    # def load_index(self, index_path=None):
    #     """Load the Chroma collection.

    #     Args:
    #         index_path: Not used for Chroma (uses collection_name instead).
    #     """
    #     try:
    #         collections = self.client.list_collections()
    #         if self.collection_name in [col.name for col in collections]:
    #             self.collection = self.client.get_collection(self.collection_name)
    #             self.logger.info(f"Loaded Chroma collection: {self.collection_name}")
    #         else:
    #             self.logger.info(f"Chroma collection {self.collection_name} does not exist; will create on next insert")
    #             self.collection = None
    #     except Exception as e:
    #         self.logger.error(f"Failed to load Chroma collection {self.collection_name}: {str(e)}")
    #         raise


    # def search(self, request_embedding):
    #     """Perform a nearest-neighbor search in the Chroma collection.

    #     Args:
    #         request_embedding (np.ndarray): Query embedding vector.

    #     Returns:
    #         np.ndarray: Array of indices of the k nearest neighbors.
    #     """
    #     if self.collection is None:
    #         raise RuntimeError(f"Chroma collection {self.collection_name} is not loaded or created")
        
    #     try:
    #         results = self.collection.query(
    #             query_embeddings=request_embedding.tolist(),
    #             n_results=self.k
    #         )
    #         ids = [int(id) for id in results['ids'][0]]
    #         return np.array(ids)
    #     except Exception as e:
    #         self.logger.error(f"Error performing search in Chroma collection: {str(e)}")
    #         raise


    # def delete_index(self):
    #     """Delete the Chroma collection."""
    #     try:
    #         collections = self.client.list_collections()
    #         if self.collection_name in [col.name for col in collections]:
    #             self.client.delete_collection(self.collection_name)
    #             self.collection = None
    #             self.logger.info(f"Deleted Chroma collection: {self.collection_name}")
    #         else:
    #             self.logger.info(f"Chroma collection {self.collection_name} does not exist")
    #     except Exception as e:
    #         self.logger.error(f"Error deleting Chroma collection: {str(e)}")
    #         raise