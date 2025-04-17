import sys

from src.utils.config_loader import load_config
from src.utils.logging_utils import setup_logger

from src.utils.mongodb_utils import insert_metadata
from src.utils.graphdb_utils import create_graph, save_graph
from src.ingestion.ingestion_manager import IngestionManager

logger = setup_logger()
config = load_config()

# Insert initial metadata into MongoDB (can be run once)
metadata_example = [
    {"function_name": "processData", "file_path": "src/utils/data_processing.py", "api_reference": "docs/api/data_processing.md"}
]
insert_metadata(metadata_example)
logger.info("Inserted initial metadata into MongoDB.")

# Create and save initial graph
graph = create_graph()
save_graph(graph)
logger.info("Created initial NetworkX graph.")

# Initialize indexers and ingestion
repo_path = "data/PyGithub"
ingestion = IngestionManager(repo_path)

# Run the indexing
ingested_data = ingestion.ingest()
logger.info("Initial data parsing and indexing complete.")

sys.exit(0)
