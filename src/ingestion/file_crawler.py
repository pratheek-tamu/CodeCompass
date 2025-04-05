import os
from src.utils.logging_utils import setup_logger, log_error

logger = setup_logger()

def crawl_files(directory, extensions=None):
    if not os.path.exists(directory):
        log_error(logger, f"Directory {directory} does not exist.")
        return []
    
    extensions = extensions or [".py", ".md"]
    matched_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                matched_files.append(os.path.join(root, file))
    return matched_files
