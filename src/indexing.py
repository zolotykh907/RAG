import json
import numpy as np
import pandas as pd
import os
import logging
from sentence_transformers import SentenceTransformer

from data_processing import *
from data_vectorize import *


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Indexing")


class Indexing:
    def __init__(self, data_path, 
                 index_path,
                 hashes_path='data/existing_hashes.json',
                 model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                 batch_size=32):
        
        self.data_path = data_path
        self.index_path = index_path
        self.hashes_path = hashes_path
        self.model_name = model_name
        self.batch_size = batch_size
        #self.model = SentenceTransformer(model_name)
        self.index = None
        self.hashes = None
        self.existing_hashes = []

    def load_data(self):
        with open(self.data_path, 'r') as f:
            data = json.load(f)

        df = pd.DataFrame(data)

        return df
    
    def check_existing_caches(self, df):
        if os.path.exists(self.hashes_path):
            with open(self.hashes_path, 'r') as f:
                existing_uid_hashes = json.load(f)

            self.existing_hashes = pd.DataFrame(existing_uid_hashes)
            print(self.existing_hashes)
        else:
            existing_uid_hashes = []
            existing_uids = df['uid'].tolist()
            existing_hashes = df['text_hash'].tolist()

            for uid, hash in zip(existing_uids, existing_hashes):
                existing_uid_hashes.append({'uid': uid, 'hash': hash})

            with open(self.hashes_path, 'w') as f:
                json.dump(existing_uid_hashes, f, ensure_ascii=False, indent=4)
    
    def check_quality(self, df):
        quality_log, df_clean = check_data_quality(df, logger)

        with open('data_quality.json', 'w') as f:
            json.dump(quality_log, f, ensure_ascii=False)

        return df_clean

    def vectorize_data(self, df):
        embeddings = create_embeddings(df['text'].tolist())
        create_faiss(embeddings)

    def run_indexing(self):
        df = self.load_data()

        df_clean = self.check_quality(df)

        self.check_existing_caches(df_clean)

        # self.existing_hashes = df_clean['text_hash'].tolist()
        # df_new = df_clean[~df_clean['text_hash'].isin(self.existing_hashes)]

        # if df_new.empty:
        #     logger.info("No new data to index.")
        #     return

        # df_new = df_new.drop('text_hash', axis=1)
        # self.vectorize_data(df_new)

I = Indexing(data_path='/Users/igorzolotyh/RAG/data/RuBQ_2.0_paragraphs.json',
             index_path='/Users/igorzolotyh/RAG/data/RuBQ_index.index',
             hashes_path='data/existing_hashes.json',)

I.run_indexing()