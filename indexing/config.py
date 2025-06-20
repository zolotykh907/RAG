import yaml

class Config:
    def __init__(self, config_file='/Users/igorzolotyh/RAG/indexing/config.yaml'):
        with open(config_file, 'r') as f:
            cfg = yaml.safe_load(f)

        self.data_path = cfg['data']['data_path']
        self.index_path = cfg['data']['index_path']
        self.hashes_path = cfg['data']['hashes_path']
        self.quality_log_path = cfg['data'].get('quality_log_path', 'data_quality.json')
        self.flag_save_data = cfg['data']['flag_save_data']
        
        self.emb_model_name = cfg['model']['emb_model_name']
        self.batch_size = cfg['model']['batch_size']
