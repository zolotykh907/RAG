import json

import pandas as pd

try:
    from logs import setup_logging  
except ImportError:
    from ..indexing.logs import setup_logging 

from ocr import OCR


class DataLoader:
    def __init__(self, config):
        self.pdf_or_image_types = ('.pdf', '.jpg', '.jpeg', '.png')
        self.logs_dir = config.logs_dir
        self.logger = setup_logging(self.logs_dir, 'DataLoader')
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

            #df = df.rename(columns={column_name, 'text'})
            self.logger.info(f'Data from {path} loaded successfully')
            return df
        except FileNotFoundError:
            self.logger.info(f'Error loaded data from {path}')
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
        ocr = OCR()
        texts = ocr.run_ocr(path)

        df = pd.DataFrame({'text': texts})
        return df
    

    def load_data(self, data):
        try:
            if isinstance(data, str):
                if data.endswith('.json'):
                    return self.from_json(data)
                elif data.endswith('.txt'):
                    return self.from_text_file(data)
                elif data.endswith(self.pdf_or_image_types):
                    return self.from_pdf_or_img(data)
                else:
                    return self.from_string(data)
            elif isinstance(data, list):
                return self.data_from_list(data)
        except Exception as e:
            self.logger.info(f'Error loaded data: {e}')
            raise