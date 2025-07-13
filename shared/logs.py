import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(logs_dir, logger_name, level='INFO'):
    """Configure logging to write to console and file.
    
    Args:
        logs_dir (str): Directory for log files
        logger_name (str): Name of the logger
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    os.makedirs(logs_dir, exist_ok=True)
    
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    log_file = os.path.join(logs_dir, f'{logger_name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024*1024*5,  # 5MB
        backupCount=1,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger