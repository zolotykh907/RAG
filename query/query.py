import json
import faiss
import os
import pandas as pd
import numpy as np
import logging
import re
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import pymorphy2


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QueryService")


class Query:
    def __init__(self, config):
        self.index_path = config.index_path
        self.processed_data_path = config.processed_data_path
        self.emb_model_name = config.emb_model_name
        self.index = None
        self.data = None
        self.texts = None
        self.k = config.k
        self.morph = pymorphy2.MorphAnalyzer()

        self.load_texts_and_index()
        
        self.download_emb_model()


    def download_emb_model(self):
        logger.info(f"Loading model {self.emb_model_name}...")
        with tqdm(total=100, desc="Downloading") as pbar:
            self.embedding_model = SentenceTransformer(
                self.emb_model_name,
                device='cpu'
            )
            pbar.update(100)
        logger.info(f"Model {self.emb_model_name} loaded successfully")


    def load_texts_and_index(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            logger.info(f'loaded index from {self.index_path}')

        with open(self.processed_data_path, 'r') as f:
            self.data = json.load(f)
            logger.info(f'loaded data from {self.processed_data_path}')

        self.texts = [item['text'] for item in self.data]
        logger.info(f'loaded {len(self.texts)} texts from data')
    

    def normalize_text(text, morph):
        text = text.strip()
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', ' ', text)

        words = text.split()
        lemmas = [morph.parse(word)[0].normal_form for word in tqdm(words) if word.isalpha()]
        
        return ' '.join(lemmas)


    def query(self, request):
        res = []

        request = self.normalize_text(request, morph=self.morph)
        request_embedding = self.embedding_model.encode([request], convert_to_numpy=True)

        d, i = self.index.search(request_embedding, self.k)
        
        for idx in i[0]:
            res.append(self.texts[idx])

        return res