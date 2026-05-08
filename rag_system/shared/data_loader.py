import json
import os
from typing import Any, List, Union

import pandas as pd

from rag_system.shared.logs import setup_logging
from rag_system.shared.ocr import OCR


class DataLoader:
    def __init__(self, config: Any) -> None:
        self.ocr_types: tuple = tuple(config.ocr_types)
        self.logs_dir: str = config.logs_dir
        self.logger = setup_logging(self.logs_dir, 'DataLoader')
        self.ocr = OCR(config)

    def from_json(self, path: str, column_name: str = 'text') -> pd.DataFrame:
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.logger.info(f"Loaded data from {path}.")

            df = pd.DataFrame(data)

            if column_name not in df.columns:
                raise ValueError(f'Column "{column_name}" not found in file {path}')

            self.logger.info(f'Data from {path} loaded successfully')
            return df
        except FileNotFoundError:
            self.logger.error(f'File not found: {path}')
            raise

    def from_text_file(self, path: str) -> pd.DataFrame:
        try:
            with open(path, 'r') as f:
                text = f.read()

            df = pd.DataFrame({'text': [text]})
            return df
        except Exception:
            self.logger.info(f'Error loading data from {path}')
            raise

    def from_string(self, string: str) -> pd.DataFrame:
        df = pd.DataFrame({'text': [string]})
        return df

    def from_list(self, data_list: List[str]) -> pd.DataFrame:
        df = pd.DataFrame({'text': data_list})
        return df

    def from_pdf_or_img(self, path: str) -> pd.DataFrame:
        texts = self.ocr.run_ocr(path)
        df = pd.DataFrame({'text': texts})
        return df

    def from_dir(self, path: str) -> pd.DataFrame:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory not found: {path}")
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Path is not a directory: {path}")

        res_df: List[pd.DataFrame] = []

        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            try:
                df = self.load_data(file_path)
                if df is not None:
                    res_df.append(df)
            except Exception as e:
                self.logger.warning(f"Error loading {file_path}: {e}")

        if not res_df:
            self.logger.warning(f"No valid files found in directory: {path}")
            return pd.DataFrame({'text': []})

        return pd.concat(res_df, ignore_index=True)

    def load_data(self, data: Union[str, List[str]]) -> pd.DataFrame:
        try:
            if isinstance(data, str):
                if os.path.isdir(data):
                    return self.from_dir(data)
                if data.endswith('.json'):
                    return self.from_json(data)
                elif data.endswith('.txt'):
                    return self.from_text_file(data)
                elif data.endswith(self.ocr_types):
                    return self.from_pdf_or_img(data)
                else:
                    return self.from_string(data)
            elif isinstance(data, list):
                return self.from_list(data)
            raise TypeError(f"Unsupported data source type: {type(data).__name__}")
        except Exception as e:
            self.logger.error(f'Error loading data: {e}')
            raise
