import logging
import os

def setup_logger(name="code-indexer", level=logging.INFO):
    logger = logging.getLogger(name)
    
    if not logger.hasHandlers():
        # Configure the logger
        formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        
        logger.setLevel(level)
        logger.addHandler(stream_handler)
    
    return logger

def enable_file_logging(logger, file_path="logs/code_indexer.log"):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s"))
    
    logger.addHandler(file_handler)

def log_exception(logger, exception):
    logger.error("An exception occurred: %s", str(exception), exc_info=True)

def log_debug(logger, message):
    logger.debug(message)

def log_info(logger, message):
    logger.info(message)

def log_warning(logger, message):
    logger.warning(message)

def log_error(logger, message):
    logger.error(message)
