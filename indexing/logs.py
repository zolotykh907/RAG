import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(logs_dir, logger_name):
        """Configure logging to write to console and file."""
        os.makedirs(logs_dir, exist_ok=True)
        
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        file_handler = RotatingFileHandler(
            logs_dir + '/' + logger_name + '.log', 
            maxBytes=1024*1024*5,
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        
        if not logger.handlers:
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
        
        return logger