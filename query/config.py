import yaml

class Config:
    def __init__(self, config_file='/Users/igorzolotyh/RAG/query/config.yaml'):
        with open(config_file, 'r') as f:
            cfg = yaml.safe_load(f)

        self.index_path = cfg['data']['index_path']
        self.processed_data_path = cfg['data']['processed_data_path']
        self.emb_model_name = cfg['models']['emb_model_name']
        self.llm = cfg['model']['llm']
        
        self.k = cfg['rag']['k']

        self.endpoint = cfg['api']['endpoint']
        self.api_title = cfg['api']['title']
        self.host = cfg['api']['host']
        self.port = cfg['apt']['port']

    