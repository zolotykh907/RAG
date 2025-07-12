import yaml
import os
from pathlib import Path


class Config:
    def __init__(self, config_file='config.yaml'):
        # Поддерживаем относительные пути
        if not os.path.isabs(config_file):
            config_file = os.path.join(os.path.dirname(__file__), config_file)
        
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
        with open(config_file, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)

        # Валидация обязательных полей
        required_fields = ['data', 'model']
        for field in required_fields:
            if field not in cfg:
                raise ValueError(f"Missing required configuration section: {field}")

        # Настройки данных
        data_config = cfg['data']
        self.data_dir = data_config.get('data_dir', './data')
        self.logs_dir = data_config.get('logs_dir', './logs')
        self.data_url = data_config.get('data_url')
        self.data_path = data_config.get('data_path', "./data/RuBQ_2.0_paragraphs.json")
        self.index_path = data_config.get('index_path', "./data/RuBQ_index.index")
        self.hashes_path = data_config.get('hashes_path', "./data/existing_hashes.json")
        self.quality_log_path = data_config.get('quality_log_path', "./logs/data_quality.json")
        self.processed_data_path = data_config.get('processed_data_path', "./data/processed_data.json")
        self.incrementation_flag = data_config.get('incrementation_flag', True)
        self.delete_data_flag = data_config.get('delete_data_flag', False)
        self.image_types = data_config.get('image_types', ['.jpg', '.jpeg', '.png'])
        self.doc_types = data_config.get('doc_types', ['.pdf', '.doc'])
        self.ocr_types = tuple(self.image_types + self.doc_types)
        
        # Настройки модели
        model_config = cfg['model']
        self.emb_model_name = model_config.get('emb_model_name', "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.batch_size = model_config.get('batch_size', 32)
        
        # Создаем необходимые директории
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
