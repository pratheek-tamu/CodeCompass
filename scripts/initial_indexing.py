import sys
import os

from src.utils.config_loader import load_config
from src.utils.logging_utils import setup_logger

from src.utils.mongodb_utils import insert_metadata
from src.utils.graphdb_utils import create_graph, save_graph, get_all_dependencies
from src.ingestion.ingestion_manager import IngestionManager
from src.indexers.codefile_indexer import CodeBERTIndexer
from src.retrievers.codefile_retriever import fetch_raw_code_by_embedding_id

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
repo_path = "data/PyGithub/PyGithub-main/github"
ingestion = IngestionManager(repo_path, indexer)

# code for parasing
ingested_data = ingestion.ingest()
logger.info("Some data parsing should have happened.")


# Searching for similar code
query_code = "class Authorization(github.GithubObject.CompletableGithubObject): This class represents Authorizations."

dependencies_result = get_all_dependencies()
print(f"dependencies result: {dependencies_result}")

embedding_ids, distances = indexer.search_similar(query_code)
print(f"Results: {embedding_ids}")
codefile = fetch_raw_code_by_embedding_id(embedding_ids[0])
print(f"Found similar code in the following files: {codefile.file_path}")
print(f"Distances: {distances}")
print(f"Best Similar match code: {codefile.raw_code}")