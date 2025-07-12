import json
import os
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import pymorphy2

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logs import setup_logging


class Query:
    """a class for preprocessing the question and semantic searching"""
    def __init__(self, config, data_base):
        """Initialize the Query service with configuration parameters.
        
        Args:
            config: configuration object with parameters.
            """
        self.data_base = data_base
        self.index_path = config.index_path
        self.logs_dir = config.logs_dir
        self.processed_data_path = config.processed_data_path
        self.emb_model_name = config.emb_model_name
        self.data = None
        self.texts = None
        self.k = config.k
        self.morph = pymorphy2.MorphAnalyzer()

        self.logger = setup_logging(self.logs_dir, 'QueryService')
        self.data_base.load_index(self.index_path)
        self.load_texts()
        #self.download_emb_model()
        self.embedding_model = self.load_local_embedding_model()
        
    def load_local_embedding_model(self):
        try:
            cache_dir = os.path.join(
                Path.home(), 
                ".cache", 
                "huggingface", 
                "hub", 
                "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2",
                "snapshots"
            )
            
            snapshots = [d for d in os.listdir(cache_dir) if os.path.isdir(os.path.join(cache_dir, d))]
            if not snapshots:
                raise FileNotFoundError(
                    f"Model {self.emb_model_name} not found in local cache {cache_dir}. "
                    )
            
            latest_snapshot = sorted(snapshots)[-1]
            model_path = os.path.join(cache_dir, latest_snapshot)
            
            self.logger.info(f"Load embedding model from local cache: {model_path}")
            return SentenceTransformer(model_path, device='cpu')
        except Exception as e:
            self.logger.error(f'Error load model from cache: {e}')
            raise

    def download_emb_model(self):
        """Download and initialize the sentence embedding model."""
        self.logger.info(f"Loading model {self.emb_model_name}...")
        try:
            with tqdm(total=100, desc="Downloading") as pbar:
                self.embedding_model = SentenceTransformer(
                    self.emb_model_name,
                    device='cpu'
                )
                pbar.update(100)
            self.logger.info(f"Model {self.emb_model_name} loaded successfully")
        except Exception as e:
            self.logger.error(f'Faild to download embedding model: {str(e)}')
            raise


    def load_texts(self):
        """Load the processed text from file."""
        if not os.path.exists(self.processed_data_path):
            raise FileNotFoundError(f"Data file not found at {self.processed_data_path}")

        try:
            with open(self.processed_data_path, 'r') as f:
                self.data = json.load(f)
                if not isinstance(self.data, list):
                    raise ValueError("Loaded data is not a list")

                self.texts = [item['text'] for item in self.data]
                self.logger.info(f'loaded {len(self.texts)} texts from {self.processed_data_path}')

                if self.data_base.index.ntotal != len(self.texts):
                    self.logger.error(f"The number of texts != the number of vectors.")
                    raise ValueError(f"The number of texts must match the number of vectors in the DB.")
        except Exception as e:
            self.logger.error(f"Failed to load data from {self.processed_data_path}: {str(e)}")
    

    def normalize_text(self, text):
        """Normalize and lemmatize input text for search.
        
        Args:
            text (str): input text to normalize.
            
        Returns:
            str: normalized text.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")

        return text.strip()


    def query(self, request):
        """Semantic search query.
        
        Args:
            request (str): search query string.
            
        Returns:
            list[str]: list of top-k most similar texts from the dataset
        """
        if not isinstance(request, str):
            raise ValueError("Request must be a string.")
        
        try:
            res = []

            request = self.normalize_text(request)
            request_embedding = self.embedding_model.encode(
                [request], 
                convert_to_numpy=True
                )

            ids = self.data_base.search(request_embedding)
            for id in ids:
                res.append(self.texts[id])

            return res
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            raise