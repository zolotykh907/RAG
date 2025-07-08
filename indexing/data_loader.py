import json

import pandas as pd

class DataLoader:
    def __init__(self):
        self.
        pass

    def from_json(self, path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.logger.info(f"Loaded data from {path}.")
                
            df = pd.DataFrame(data)
            
            return df
        except FileNotFoundError:
            self.logger.error(f"File {path} not found.")
            raise

    def from_text_file(self, path):
        try:
            with open(path, 'r') as f:
                text = f.read()

            df = pd.DataFrame({'uid': ['text_file'], 'text': [text]})
            return df
        except Exception as e:
            print(f"Error adding embeddings or saving index: {e}")
            raise

    def from_string(self, s):
        df = pd.DataFrame({'uid': ['str'], 'text': [s]})



        