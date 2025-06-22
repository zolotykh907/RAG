import json
import os
import logging

import numpy as np
import pandas as pd
import faiss
import requests
from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm
import pymorphy2

from data_processing import normalize_text, check_data_quality
from data_vectorize import create_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Indexing")


class Indexing:
    """Manage text indexing process with embedding creation and FAISS index maintenance."""
    def __init__(self, config):
        """Initialize Indexing with configuration parameters.

        Args:
            config : configuration object with parameters:
        """
        self.data_dir = config.data_dir
        self.logs_dir = config.logs_dir
        self.data_url = config.data_url
        self.data_path = config.data_path
        self.index_path = config.index_path
        self.hashes_path = config.hashes_path
        self.processed_data_path = config.processed_data_path
        self.emb_model_name = config.emb_model_name
        self.batch_size = config.batch_size
        self.index = None
        self.existing_hashes = []
        self.flag_save_data = config.flag_save_data
        self.quality_log_path = config.quality_log_path
        self.morph = pymorphy2.MorphAnalyzer()

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self.download_emb_model()

    def download_emb_model(self):
        """Download of embedding model."""
        logger.info(f"Loading model {self.emb_model_name}...")
        try:
            with tqdm(total=100, desc="Downloading") as pbar:
                self.embedding_model = SentenceTransformer(
                    self.emb_model_name,
                    device='cpu'
                )
                pbar.update(100)
            logger.info(f"Model {self.emb_model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели {self.emb_model_name}: {e}")
            raise


    def download_data(self):
        """Download and sace data from URL"""
        if not os.path.exists(self.data_path):
            logger.info(f'Downloading data from {self.data_url}.')
            response = requests.get(self.data_url)
            response.raise_for_status()

            with open(self.data_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Saved data to {self.data_path}.")
        else:
            logger.info(f'File {self.data_path} exists.')


    def load_data(self, path):
        """Load data from .json file and convert to DataFrame.

        Args:
            path (str): path to .json file.

        Returns:
            DataFrame: DataFrame with loaded data.
        """
        self.download_data()
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded data from {path}.")

            df = pd.DataFrame(data)
            return df
        except FileNotFoundError:
            logger.error(f"File {path} not found.")
            raise
    

    def check_existing_index(self):
        """"Load existing index FAISS."""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            logger.info(f"Loaded existing index from {self.index_path}.")
    

    def check_existing_haches(self):
        """Load or create texts hashes."""
        if os.path.exists(self.hashes_path):
            with open(self.hashes_path, 'r') as f:
                existing_uid_hashes = json.load(f)

            self.existing_hashes = pd.DataFrame(existing_uid_hashes)
            logger.info(f"Loaded existing hashes from {self.hashes_path}.")
        else:
            logger.info(f"No existing hashes found at {self.hashes_path}. Creating a new DataFrame.")

            self.existing_hashes = pd.DataFrame(columns=['uid', 'hash'])
    

    def update_existing_hashes(self, df):
        """Update existing hashes with new data.

        Args:
            df (DataFrame): DataFrame with uid and text_hash.
        """
        new_uids = df['uid'].tolist()
        new_hashes = df['text_hash'].tolist()
        self.existing_hashes = pd.concat([self.existing_hashes, pd.DataFrame({'uid': new_uids, 'hash': new_hashes})], ignore_index=True)
        logger.info(f"Updated existing hashes.")


    def check_quality(self, df):
        """Data quality check and save results.

        Args:
            df (DataFrame): DataFrame with texts.

        Returns:
            DataFrame: clean DataFrame after quality check.
        """
        quality_log, df_clean = check_data_quality(df)
        logger.info(f"Data quality check completed. {len(df_clean)} texts passed the quality check.")

        with open(self.quality_log_path, 'w') as f:
            json.dump(quality_log, f, ensure_ascii=False)

        return df_clean
    
    
    def save_data(self, df):
        """Save processed data to file, merging with existing data.

        Args:
            df (DataFrame): DataFrame to save.
        """
        if os.path.exists(self.processed_data_path):
            processed_df = self.load_data(path=self.processed_data_path)
            combined_df = pd.concat([processed_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['uid'])
            combined_df.to_json(self.processed_data_path, orient='records', force_ascii=False, indent=4)
        else:
            df.to_json(self.processed_data_path, orient='records', force_ascii=False, indent=4)


    def run_indexing(self):
        """Full indexing pipeline."""
        df = self.load_data(path=self.data_path)

        df_clean = self.check_quality(df)

        self.check_existing_index()
        self.check_existing_haches(df_clean)

        df_new = df_clean[~df_clean['text_hash'].isin(self.existing_hashes['hash'].tolist())]

        if df_new.empty:
            logger.info("No new data to index.")
            return
        
        self.update_existing_hashes(df_new)

        df_new = df_new.drop('text_hash', axis=1)
        logger.info(f"Found {len(df_new)} new texts to index.")

        if self.flag_save_data:
            self.save_data(df_new)

        logger.info(f'Text normalization...')
        df_new['text'] = df_new['text'].apply(lambda x: normalize_text(x, morph=self.morph))
        
        embeddings = create_embeddings(df_new['text'].tolist(), self.embedding_model, batch_size=self.batch_size)

        try:
            if self.index is None:
                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dim)

            self.index.add(np.array(embeddings, dtype=np.float32))
            faiss.write_index(self.index, self.index_path)
            logger.info(f"Index saved to {self.index_path}.")
        except Exception as e:
            logger.error(f"Error when adding or saving the index: {e}")
            raise

        with open(self.hashes_path, 'w') as f:
            json.dump(self.existing_hashes.to_dict('records'), f, ensure_ascii=False, indent=4)
            logger.info(f"Saved updated hashes to {self.hashes_path}.")