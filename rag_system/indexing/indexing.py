import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_system.indexing.data_processing import check_data_quality
from rag_system.indexing.data_processing import compute_text_hash
from rag_system.indexing.data_processing import normalize_text
from rag_system.indexing.data_vectorize import create_embeddings
from rag_system.indexing.data_vectorize import load_embeddings
from rag_system.indexing.data_vectorize import save_embeddings
from rag_system.shared.logs import setup_logging


class Indexing:
    """Manage text indexing process with embedding creation and FAISS index maintenance."""
    def __init__(self, config, data_loader, data_base):
        """Initialize Indexing with configuration parameters.

        Args:
            config: Configuration object with all necessary parameters
            data_loader: DataLoader instance for loading various data formats
            data_base: FaissDB instance for index management
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
        self.incrementation_flag = config.incrementation_flag
        self.delete_data_flag = config.delete_data_flag

        self.data_base = data_base
        self.data_loader = data_loader

        self.existing_hashes = []
        self.embeddings_path = os.path.join(config.data_dir, "embeddings.npy")

        self.logger = setup_logging(self.logs_dir, 'IndexingService')
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                                            chunk_overlap=0)

        os.makedirs(self.data_dir, exist_ok=True)

        self.emb_model = self.load_local_embedding_model()

        if self.incrementation_flag:
            self.load_existing_hashes()

    def load_local_embedding_model(self):
        """Load model from local HuggingFace cache."""
        try:
            cache_dir = os.path.join(
                Path.home(),
                ".cache",
                "huggingface",
                "hub",
                f"models--{self.emb_model_name.replace('/', '--')}",
                "snapshots"
            )

            if not os.path.exists(cache_dir):
                return self.download_embedding_model()

            snapshots = [d for d in os.listdir(cache_dir)
                        if os.path.isdir(os.path.join(cache_dir, d))]

            if not snapshots:
                raise FileNotFoundError(
                    f"Model {self.emb_model_name} not found in local cache {cache_dir}."
                )

            latest_snapshot = sorted(snapshots)[-1]
            model_path = os.path.join(cache_dir, latest_snapshot)

            self.logger.info(f"Loading embedding model from local cache: {model_path}")
            return SentenceTransformer(model_path, device='cpu')
        except Exception as e:
            self.logger.error(f'Error loading model from cache: {e}')
            raise

    def download_embedding_model(self):
        """Download embedding model from Hugging Face."""
        self.logger.info(f"Downloading model {self.emb_model_name}...")
        try:
            emb_model = SentenceTransformer(
                self.emb_model_name,
                device='cpu'
            )
            self.logger.info(f"Model {self.emb_model_name} loaded successfully")
            return emb_model
        except Exception as e:
            self.logger.error(f"Failed to download model {self.emb_model_name}: {e}")
            raise

    def download_data(self):
        """Download and save data from URL."""
        if not os.path.exists(self.data_path):
            self.logger.info(f'Downloading data from {self.data_url}.')
            try:
                response = requests.get(self.data_url)
                response.raise_for_status()

                with open(self.data_path, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"Saved data to {self.data_path}.")
            except Exception as e:
                self.logger.error(f"Failed to download data: {e}")
                raise
        else:
            self.logger.info(f'File {self.data_path} exists.')

    def load_data(self, data_source):
        """Load data from various sources."""
        try:
            df = self.data_loader.load_data(data_source)
            self.logger.info(f"Loaded {len(df)} records from data source")
            return df
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            raise

    def load_existing_hashes(self):
        """Load texts hashes from processed data file."""
        if os.path.exists(self.processed_data_path):
            with open(self.processed_data_path, 'r') as f:
                processed_data = json.load(f)

            if processed_data:
                df = pd.DataFrame(processed_data)
                self.existing_hashes = df['hash'].tolist()
                self.logger.info(f"Loaded {len(self.existing_hashes)} existing hashes")
            else:
                self.existing_hashes = []
                self.logger.info("No existing hashes found")
        else:
            self.existing_hashes = []
            self.logger.info(f"No existing hashes found at {self.processed_data_path}.")

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

    def save_processed_data(self, df):
        """Save processed data, merging with existing if incrementing."""
        try:
            if self.incrementation_flag and os.path.exists(self.processed_data_path):
                with open(self.processed_data_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

                existing_df = pd.DataFrame(existing_data)
                combined_df = pd.concat([existing_df, df], ignore_index=True)

                combined_df = combined_df.drop_duplicates(subset=['hash'], keep='first')
            else:
                combined_df = df

            combined_df.to_json(
                self.processed_data_path,
                orient='records',
                force_ascii=False,
                indent=2
            )

            self.logger.info(f"Saved {len(combined_df)} chunks")

        except Exception as e:
            self.logger.error(f"Failed to save processed data: {e}")
            raise

    def split_to_chunks(self, df, source_file=None):
        """Split texts into chunks.

        Args:
            df (DataFrame): DataFrame with 'text' column.
            source_file (str): Optional source filename for tracking

        Returns:
            DataFrame: new DataFrame with chunks.
        """
        from datetime import datetime

        res = []
        for _, row in df.iterrows():
            chunks = self.text_splitter.split_text(row['text'])
            for chunk in chunks:
                res.append({
                    'text': chunk,
                    'source': source_file if source_file else 'unknown',
                    'timestamp': datetime.now().isoformat()
                })

        res_df = pd.DataFrame(res)
        self.logger.info(f"Created {len(res)} chunks from {len(df)} texts")
        return res_df

    def run_indexing(self, data=None):
        try:
            if data is None:
                if self.data_url:
                    self.download_data()
                data = self.data_path

            # Extract source filename
            source_file = os.path.basename(data) if data else 'unknown'

            if not self.incrementation_flag:
                self.clear_existing_data()
                self.existing_hashes = []
            else:
                self.load_existing_hashes()

            df = self.load_data(data_source=data)
            df_clean = self.check_quality(df)

            if not self.incrementation_flag:
                df_new = df_clean
            else:
                df_new = df_clean[~df_clean['hash'].isin(self.existing_hashes)]

            if df_new.empty:
                if not self.incrementation_flag:
                    self.logger.info("No texts to index.")
                else:
                    self.logger.info("No new unique texts to index.")
                return

            df_chunks = self.split_to_chunks(df_new, source_file=source_file)
            df_chunks['hash'] = df_chunks['text'].apply(compute_text_hash)

            if not self.incrementation_flag:
                df_chunks_new = df_chunks
            else:
                df_chunks_new = df_chunks[~df_chunks['hash'].isin(self.existing_hashes)]

            if df_chunks_new.empty:
                if not self.incrementation_flag:
                    self.logger.info("No chunks to index.")
                else:
                    self.logger.info("No new unique chunks to index.")
                return

            new_hashes = df_chunks_new['hash'].tolist()
            if self.incrementation_flag:
                self.existing_hashes.extend(new_hashes)
            else:
                self.existing_hashes = new_hashes

            self.logger.info(f"Found {len(df_chunks_new)} new chunks to index.")

            self.logger.info("Normalizing chunk texts...")
            df_chunks_new['text'] = df_chunks_new['text'].apply(
                lambda x: normalize_text(x)
            )

            self.save_processed_data(df_chunks_new)

            new_embeddings = create_embeddings(df_chunks_new['text'].tolist(),
                                               self.emb_model,
                                               batch_size=self.batch_size)

            if self.incrementation_flag:
                self.data_base.load_index()

                existing_embeddings = load_embeddings(self.embeddings_path)
                if existing_embeddings is not None:
                    all_embeddings = np.vstack([existing_embeddings, new_embeddings])
                    self.logger.info(
                        f"Combined embeddings: existing {existing_embeddings.shape[0]} + "
                        f"new {new_embeddings.shape[0]} = {all_embeddings.shape[0]}"
                    )
                else:
                    all_embeddings = new_embeddings
                    self.logger.info("Created new embeddings (no existing found)")

                save_embeddings(all_embeddings, self.embeddings_path)

                self.data_base.create_index(new_embeddings, replace=False)
            else:
                save_embeddings(new_embeddings, self.embeddings_path)
                self.data_base.create_index(new_embeddings, replace=True)
                self.logger.info("Created new embeddings")

        except Exception as e:
            if self.delete_data_flag:
                self.logger.error(f"Indexing error: {e}")
                if os.path.exists(self.processed_data_path):
                    self.clear_existing_data()
                raise

    def clear_existing_data(self):
        """Clear existing processed data and embeddings."""
        files_to_remove = [
            self.processed_data_path,
            self.embeddings_path,
            self.index_path
        ]

        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Removed existing file: {file_path}")

        if not self.incrementation_flag:
            self.existing_hashes = []
            self.logger.info("Cleared existing hashes (incrementation disabled)")

    def clear_data(self):
        """Clear all indexed data (alias for clear_existing_data)."""
        self.clear_existing_data()
