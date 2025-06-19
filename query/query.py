import json
import faiss
import os
import pandas as pd
import numpy as np
import logging
import re
from sentence_transformers import SentenceTransformer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QueryService")


class Query:
    def __init__(self, index_path, data_path, emb_model_name, k=5):
        self.index_path = index_path
        self.data_path = data_path
        self.emb_model_name = emb_model_name
        self.index = None
        self.embedding_model = SentenceTransformer(self.emb_model_name)
        self.data = None
        self.texts = None
        self.k = k

        self.load_texts_and_index()
        

    def load_texts_and_index(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            logger.info(f'loaded index from {self.index_path}')

        with open(self.data_path, 'r') as f:
            self.data = json.load(f)
            logger.info(f'loaded data from {self.data_path}')

        self.texts = [item['text'] for item in self.data]
        logger.info(f'loaded {len(self.texts)} texts from data')

    def normalize_text(self, text):
        text = text.strip()
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        return text

    def query(self, request):
        res = []

        request = self.normalize_text(request)
        request_embedding = self.embedding_model.encode([request], convert_to_numpy=True)

        d, i = self.index.search(request_embedding, self.k)
        
        for idx in i[0]:
            res.append(self.texts[idx])

        return res


# q = Query(index_path='/Users/igorzolotyh/RAG/data/RuBQ_index.index',
#           data_path='/Users/igorzolotyh/RAG/data/good_texts.json',
#           emb_model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
#           )

# res = q.query('')
# print(res[0])