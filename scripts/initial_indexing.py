import sys
import os

from src.utils.config_loader import load_config
from src.utils.logging_utils import setup_logger

from src.utils.mongodb_utils import get_mongodb_client, insert_metadata
from src.utils.graphdb_utils import create_graph, save_graph
from src.ingestion.ingestion_manager import IngestionManager

logger = setup_logger()
config = load_config()

metadata_example = [
    {"function_name": "processData", "file_path": "src/utils/data_processing.py", "api_reference": "docs/api/data_processing.md"}
]
insert_metadata(metadata_example)
logger.info("Inserted initial metadata into MongoDB.")

graph = create_graph()
save_graph(graph)
logger.info("Created initial NetworkX graph.")

# code for parasing
repo_path = "data/PyGithub/PyGithub-main/github"
ingestion = IngestionManager(repo_path)
ingested_data = ingestion.ingest()
logger.info("Some data parsing should have happened.")