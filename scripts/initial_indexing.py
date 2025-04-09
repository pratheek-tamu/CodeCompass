import sys
import os

from src.utils.config_loader import load_config
from src.utils.logging_utils import setup_logger

from src.utils.mongodb_utils import insert_metadata
from src.utils.graphdb_utils import create_graph, save_graph, get_all_dependencies
from src.ingestion.ingestion_manager import IngestionManager
from src.indexers.codefile_indexer import CodeBERTIndexer
from src.retrievers.codefile_retriever import fetch_code_file_by_file_path

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

# initialization for dependency creation and injection
indexer = CodeBERTIndexer()
repo_path = "data/PyGithub/"
ingestion = IngestionManager(repo_path, indexer)

# code for parasing
ingested_data = ingestion.ingest()
logger.info("Some data parsing should have happened.")


# Searching for similar code
query_code = "class Authorization(github.GithubObject.CompletableGithubObject): This class represents Authorizations."

dependencies_result = get_all_dependencies()
print(f"dependencies result: {dependencies_result}")

result_paths, distances = indexer.search_similar(query_code)
print(f"Results: {result_paths}")
codefile = fetch_code_file_by_file_path(result_paths[0])
print(f"Found similar code in the following files: {result_paths}")
print(f"Distances: {distances}")
print(f"Best Similar match code: {codefile.raw_code}")