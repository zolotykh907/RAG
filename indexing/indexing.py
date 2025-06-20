import json
import numpy as np
import pandas as pd
import os
import logging
import faiss
from sentence_transformers import SentenceTransformer

from data_processing import *
from data_vectorize import *
from config import Config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Indexing")


class Indexing:
    def __init__(self, config):
        self.data_path = config.data_path
        self.index_path = config.index_path
        self.hashes_path = config.hashes_path
        self.processed_data_path = config.processed_data_path
        self.emb_model_name = config.emb_model_name
        self.batch_size = config.batch_size
        self.index = None
        self.existing_hashes = []
        self.embedding_model = SentenceTransformer(self.emb_model_name)
        self.flag_save_data = config.flag_save_data


    def load_data(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
            logger.info(f"Loaded data from {path}.")

        df = pd.DataFrame(data)

        return df
    

    def check_existing_index(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            logger.info(f"Loaded existing index from {self.index_path}.")
    

    def check_existing_caches(self, df):
        if os.path.exists(self.hashes_path):
            with open(self.hashes_path, 'r') as f:
                existing_uid_hashes = json.load(f)

            self.existing_hashes = pd.DataFrame(existing_uid_hashes)
            logger.info(f"Loaded existing hashes from {self.hashes_path}.")
        else:
            logger.info(f"No existing hashes found at {self.hashes_path}. Creating a new DataFrame.")

            self.existing_hashes = pd.DataFrame(columns=['uid', 'hash'])
    

    def update_existing_hashes(self, df):
        new_uids = df['uid'].tolist()
        new_hashes = df['text_hash'].tolist()
        self.existing_hashes = pd.concat([self.existing_hashes, pd.DataFrame({'uid': new_uids, 'hash': new_hashes})], ignore_index=True)
        logger.info(f"Updated existing hashes.")


    def check_quality(self, df):
        quality_log, df_clean = check_data_quality(df, logger)
        logger.info(f"Data quality check completed. {len(df_clean)} texts passed the quality check.")

        with open('data_quality.json', 'w') as f:
            json.dump(quality_log, f, ensure_ascii=False)

        return df_clean
    
    
    def save_data(self, df):
        if os.path.exists(self.processed_data_path):
            processed_df = self.load_data(path=self.processed_data_path)
            combined_df = pd.concat([processed_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['uid'])
            combined_df.to_json(self.processed_data_path, orient='records', force_ascii=False, indent=4)
        else:
            df.to_json(self.processed_data_path, orient='records', force_ascii=False, indent=4)


    def run_indexing(self):
        df = self.load_data(path=self.data_path)

        df_clean = self.check_quality(df)

        self.check_existing_index()
        self.check_existing_caches(df_clean)

        df_new = df_clean[~df_clean['text_hash'].isin(self.existing_hashes['hash'].tolist())]

        if df_new.empty:
            logger.info("No new data to index.")
            return
        
        self.update_existing_hashes(df_new)

        df_new = df_new.drop('text_hash', axis=1)
        logger.info(f"Found {len(df_new)} new texts to index.")

        if self.flag_save_data:
            self.save_data(df_new)

        df_new['text'] = df_new['text'].apply(normalize_text)
        
        embeddings = create_embeddings(df_new['text'].tolist(), self.embedding_model, batch_size=self.batch_size)

        if self.index is None:
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)

        self.index.add(np.array(embeddings, dtype=np.float32))
        faiss.write_index(self.index, self.index_path)

        with open(self.hashes_path, 'w') as f:
            json.dump(self.existing_hashes.to_dict('records'), f, ensure_ascii=False, indent=4)
            logger.info(f"Saved updated hashes to {self.hashes_path}.")


# config = Config()
# I = Indexing(config)
# I.run_indexing()