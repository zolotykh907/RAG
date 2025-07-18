import yaml

class Config:
    def __init__(self, config_file='query/config.yaml'):
        with open(config_file, 'r') as f:
            cfg = yaml.safe_load(f)

        self.index_path = cfg['data']['index_path']
        self.logs_dir = cfg['data']['logs_dir']
        self.processed_data_path = cfg['data']['processed_data_path']
        self.image_types = cfg['data']['image_types']
        self.doc_types = cfg['data']['doc_types']
        self.ocr_types = tuple(self.image_types + self.doc_types)

        self.emb_model_name = cfg['models']['emb_model_name']
        self.llm = cfg['models']['llm']
        self.prompt_template = cfg['models']['prompt_template']

        
        self.k = cfg['rag']['k']

        self.endpoint = cfg['api']['endpoint']
        self.api_title = cfg['api']['title']
        self.host = cfg['api']['host']
        self.port = cfg['api']['port']
        self.ollama_host = cfg['api']['ollama_host']

    