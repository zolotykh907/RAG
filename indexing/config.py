import yaml


class Config:
    def __init__(self, config_file='indexing/config.yaml'):
        with open(config_file, 'r') as f:
            cfg = yaml.safe_load(f)

        self.data_dir = cfg['data']['data_dir']
        self.logs_dir = cfg['data']['logs_dir']
        self.data_url = cfg['data']['data_url']
        self.data_path = cfg['data']['data_path']
        self.index_path = cfg['data']['index_path']
        self.hashes_path = cfg['data']['hashes_path']
        self.quality_log_path = cfg['data']['quality_log_path']
        self.processed_data_path = cfg['data']['processed_data_path']
        self.incrementation_flag = cfg['data']['incrementation_flag']
        self.delete_data_flag = cfg['data']['delete_data_flag']
        self.image_types = cfg['data']['image_types']
        self.doc_types = cfg['data']['doc_types']
        self.ocr_types = self.image_types + self.doc_types
        
        self.emb_model_name = cfg['model']['emb_model_name']
        self.batch_size = cfg['model']['batch_size']
