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
        required_sections = ['data', 'models', 'rag', 'api']
        for section in required_sections:
            if section not in cfg:
                raise ValueError(f"Missing required configuration section: {section}")

        # Настройки данных
        data_config = cfg['data']
        self.index_path = data_config.get('index_path', "./data/RuBQ_index.index")
        self.logs_dir = data_config.get('logs_dir', './logs')
        self.processed_data_path = data_config.get('processed_data_path', "./data/processed_data.json")
        
        # Настройки моделей
        models_config = cfg['models']
        self.emb_model_name = models_config.get('emb_model_name', "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.llm = models_config.get('llm', 'llama3')
        self.prompt_template = models_config.get('prompt_template', '')
        
        # Настройки RAG
        rag_config = cfg['rag']
        self.k = rag_config.get('k', 5)
        
        # Настройки API
        api_config = cfg['api']
        self.endpoint = api_config.get('endpoint', '/query')
        self.api_title = api_config.get('title', 'RAG Query API')
        self.host = api_config.get('host', '0.0.0.0')
        self.port = api_config.get('port', 8000)
        self.ollama_host = api_config.get('ollama_host', 'http://localhost:11434')
        
        # Создаем необходимые директории
        os.makedirs(self.logs_dir, exist_ok=True)

    