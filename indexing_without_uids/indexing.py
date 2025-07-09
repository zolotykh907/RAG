import json
import os

import numpy as np
import pandas as pd
import faiss
import requests
from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pymorphy2

from data_processing import normalize_text, check_data_quality, compute_text_hash
from data_vectorize import create_embeddings
try:
    from logs import setup_logging  
except ImportError:
    from ..indexing.logs import setup_logging 

class Indexing:
    """Manage text indexing process with embedding creation and FAISS index maintenance."""
    def __init__(self, config, data_loader):
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
        self.batch_size = config.batch_size
        self.quality_log_path = config.quality_log_path
        self.emb_model_name = config.emb_model_name
        self.index = None
        self.existing_hashes = []
        self.morph = pymorphy2.MorphAnalyzer()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, 
                                                            chunk_overlap=0)
        self.data_loader = data_loader
        self.logger = setup_logging(self.logs_dir, 'IndexingService')

        os.makedirs(self.data_dir, exist_ok=True)

        if self.data_url:
            self.download_data()
        #self.download_emb_model()
        

    def download_emb_model(self):
        """Download of embedding model."""
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
            self.logger.error(f"Ошибка загрузки модели {self.emb_model_name}: {e}")
            raise


    def download_data(self):
        """Download and sace data from URL"""
        if not os.path.exists(self.data_path):
            self.logger.info(f'Downloading data from {self.data_url}.')
            response = requests.get(self.data_url)
            response.raise_for_status()

            with open(self.data_path, 'wb') as f:
                f.write(response.content)
            self.logger.info(f"Saved data to {self.data_path}.")
        else:
            self.logger.info(f'File {self.data_path} exists.')


    def load_data(self, path):
        """Load data from .json file and convert to DataFrame.

        Args:
            path (str): path to .json file.

        Returns:
            DataFrame: DataFrame with loaded data.
        """
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.logger.info(f"Loaded data from {path}.")
                
            df = pd.DataFrame(data)
            return df
        except FileNotFoundError:
            self.logger.error(f"File {path} not found.")
            raise
    

    def check_existing_index(self):
        """"Load existing index FAISS."""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self.logger.info(f"Loaded existing index from {self.index_path}.")
    

    def check_existing_hashes(self):
        """Load or create texts hashes."""
        if os.path.exists(self.processed_data_path):
            with open(self.processed_data_path, 'r') as f:
                processed_data = json.load(f)

            self.existing_hashes = pd.DataFrame(processed_data)['hash'].tolist()
            self.logger.info(f"Loaded existing hashes from {self.processed_data_path}.")
        else:
            self.logger.info(f"No existing hashes found at {self.processed_data_path}. Creating a new DataFrame.")


    def check_quality(self, df):
        """Data quality check and save results.

        Args:
            df (DataFrame): DataFrame with texts.

        Returns:
            DataFrame: clean DataFrame after quality check.
        """
        quality_log, df_clean = check_data_quality(df)
        self.logger.info(f"Data quality check completed. {len(df_clean)} texts passed the quality check.")

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
            combined_df.to_json(self.processed_data_path, orient='records', force_ascii=False, indent=4)
        else:
            df.to_json(self.processed_data_path, orient='records', force_ascii=False, indent=4)
    

    def split_to_chunks(self, df):
        """Split texts into chunks.

        Args:
            df (DataFrame): DataFrame with 'uid' and 'text'.

        Returns:
            DataFrame: new DataFrame with chunks.
        """
        res = []
        for _, row in df.iterrows():
            chunks = self.text_splitter.split_text(row['text'])
            for i, chunk in enumerate(chunks):
                res.append({
                    'text': chunk
                })

        res_df = pd.DataFrame(res)
        return res_df


    def run_indexing(self, data=None, rewriting_flag=False):
        try:
            if data:
                df = self.data_loader.load_data(data=data)
            else:
                df = self.data_loader.load_data(data=self.data_path)

            df_clean = self.check_quality(df)
            
            if not rewriting_flag:
                self.check_existing_index()
                self.check_existing_hashes()
            else:
                if os.path.exists(self.processed_data_path):
                    os.remove(self.processed_data_path)

            df_new = df_clean[~df_clean['hash'].isin(self.existing_hashes)]

            if df_new.empty:
                self.logger.info("No new unique texts to index.")

            df_chunks = self.split_to_chunks(df_new)
            df_chunks['hash'] = df_chunks['text'].apply(compute_text_hash)

            df_chunks_new = df_chunks[~df_chunks['hash'].isin(self.existing_hashes)]

            if df_chunks_new.empty:
                self.logger.info("No new unique chunks to index.")

            new_hashes = df_chunks_new['hash'].tolist()
            self.existing_hashes.extend(new_hashes)

            self.logger.info(f"Found {len(df_chunks_new)} new chunks to index.")

            self.logger.info("Normalizing chunk texts...")
            df_chunks_new['text'] = df_chunks_new['text'].apply(lambda x: normalize_text(x, morph=self.morph))

            self.logger.info(f"Saved updated hashes and texts to {self.processed_data_path}.")

            embeddings = create_embeddings(df_chunks_new['text'].tolist(), self.embedding_model, batch_size=self.batch_size)

            try:
                if self.index is None:
                    dim = embeddings.shape[1]
                    self.index = faiss.IndexFlatL2(dim)
                    self.logger.info(f"Created new FAISS index with dimension {dim}.")

                self.index.add(np.array(embeddings, dtype=np.float32))
                faiss.write_index(self.index, self.index_path)
                self.logger.info(f"FAISS index saved to {self.index_path}.")
            except Exception as e:
                self.logger.error(f"Error adding embeddings or saving index: {e}")
                raise
        except Exception as e:
            self.logger.error(f"Error {e}")
            # if os.path.exists(self.processed_data_path):
            #     os.remove(self.processed_data_path)
            raise