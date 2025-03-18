from src.utils.config_loader import load_config
from src.utils.logging_utils import setup_logger

from src.utils.mongodb_utils import get_mongodb_client, insert_metadata
from src.utils.graphdb_utils import create_graph, save_graph

logger = setup_logger()
config = load_config()

mongo_client = get_mongodb_client(config["mongodb"]["uri"])
metadata_example = [
    {"function_name": "processData", "file_path": "src/utils/data_processing.py", "api_reference": "docs/api/data_processing.md"},
]
insert_metadata(mongo_client, config["mongodb"]["database"], config["mongodb"]["metadata_collection"], metadata_example)
logger.info("Inserted initial metadata into MongoDB.")

graph = create_graph()
save_graph(graph, config["graphdb"]["graph_storage_path"])
logger.info("Created initial NetworkX graph.")
