import json
import os
import pandas as pd

try:
    from logs import setup_logging  
except ImportError:
    from ..indexing.logs import setup_logging 

from ocr import OCR


class DataLoader:
    def __init__(self, config):
        self.ocr_types = config.image_types + config.doc_types
        self.logs_dir = config.logs_dir
        self.logger = setup_logging(self.logs_dir, 'DataLoader')
        self.ocr = OCR(config)
        pass


    def from_json(self, path, column_name='text'):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.logger.info(f"Loaded data from {path}.")
                
            df = pd.DataFrame(data)

            if column_name not in df.columns:
                self.logger.info(f'Column "{column_name}" not found in file {path}')
                raise

            self.logger.info(f'Data from {path} loaded successfully')
            return df
        except FileNotFoundError:
            self.logger.error(f'File not found: {path}')
            raise


    def from_text_file(self, path):
        try:
            with open(path, 'r') as f:
                text = f.read()

            df = pd.DataFrame({'text': [text]})
            return df
        except Exception as e:
            self.logger.info(f'Error loaded data from {path}')
            raise


    def from_string(self, string):
        df = pd.DataFrame({'text': [string]})
        return df


    def from_list(self, list):
        df = pd.DataFrame({'text': list})
        return df


    def from_pdf_or_img(self, path):
        texts = self.ocr.run_ocr(path)

        df = pd.DataFrame({'text': texts})
        return df
    

    def from_dir(self, path):
        if os.path.exists(path):
            res_df = []

            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                try:
                    df = self.load_data(file_path)
                    res_df.append(df)
                except Exception as e:
                    self.logger.warning(f"Error download {file_path}: {e}")

            return pd.concat(res_df, ignore_index=True)
            

    def load_data(self, data):
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
                return self.data_from_list(data)
        except Exception as e:
            self.logger.info(f'Error loaded data: {e}')
            raise