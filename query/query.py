import json
import os
import re
import logging
from logging.handlers import RotatingFileHandler

import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import pymorphy2

from query.logs import setup_logging


class Query:
    """a class for preprocessing the question and semantic searching"""
    def __init__(self, config):
        """Initialize the Query service with configuration parameters.
        
        Args:
            config: configuration object with parameters.
            """
        self.index_path = config.index_path
        self.logs_dir = config.logs_dir
        self.processed_data_path = config.processed_data_path
        self.emb_model_name = config.emb_model_name
        self.index = None
        self.data = None
        self.texts = None
        self.k = config.k
        self.morph = pymorphy2.MorphAnalyzer()

        self.logger = setup_logging(self.logs_dir, 'QueryService')
        self.load_texts_and_index()
        self.download_emb_model()
        

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


    def load_texts_and_index(self):
        """Load the FAISS index and processed text data from files."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"Index file not found at {self.index_path}")
        
        if not os.path.exists(self.processed_data_path):
            raise FileNotFoundError(f"Data file not found at {self.processed_data_path}")
        
        try:
            self.index = faiss.read_index(self.index_path)
            self.logger.info(f'Index loaded from {self.index_path}')
        except Exception as e:
            self.logger.error(f"Failed to load FAISS index from {self.index_path}: {str(e)}")
            raise

        try:
            with open(self.processed_data_path, 'r') as f:
                self.data = json.load(f)
                if not isinstance(self.data, list):
                    raise ValueError("Loaded data is not a list")
                self.logger.info(f'loaded data from {self.processed_data_path}')

                self.texts = [item['text'] for item in self.data]
                self.logger.info(f'loaded {len(self.texts)} texts from data')
        except Exception as e:
            self.logger.error(f'Failed to load data from {self.texts}: {str(e)}')
    

    def normalize_text(self, text):
        """Normalize and lemmatize input text for search.
        
        Args:
            text (str): input text to normalize.
            
        Returns:
            str: normalized text.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")
        text = text.strip()
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', ' ', text)

        words = text.split()
        lemmas = [self.morph.parse(word)[0].normal_form 
                  for word in tqdm(words) 
                  if word.isalpha()]
        
        return ' '.join(lemmas)


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

            d, i = self.index.search(request_embedding, self.k)
            for idx in i[0]:
                res.append(self.texts[idx])

            return res
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            raise