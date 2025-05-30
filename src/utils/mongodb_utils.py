from pymongo import MongoClient

from .logging_utils import setup_logger
from .config_loader import load_config

# Setup Logging
logger = setup_logger()

# Load configuration once when module is imported
_config = load_config()["mongodb"]
_client = MongoClient(_config["uri"], maxPoolSize=50)
_db = _client[_config["database"]]
_collection = _db[_config["metadata_collection"]]

def get_collection():
    return _collection

def get_mongodb_client(uri=None):
    if uri is None:
        uri = _config["uri"]
    return MongoClient(uri, maxPoolSize=50)

def insert_code_file(code_content):
    return _collection.insert_one(code_content)

def fetch_all_raw_code():
    """Fetch raw_code from all documents of type 'CodeFile.class'."""
    query = {"type": "CodeFile.class"}
    projection = {
        "_id": 0,  # Exclude the _id field
        "file_path": 1,  # Include file_path
        "raw_code": 1,  # Include raw_code
        "cleaned_code": 1,  # Include cleaned_code
        "docstrings": 1,  # Include docstrings
        "entities": 1,  # Include entities
        "function_calls": 1,  # Include function_calls
        "imports": 1,  # Include imports
        "global_variables": 1,  # Include global_variables
        "embedding_ids": 1,  # Include embedding_ids
        "type": 1,  # Include type
    }
    return list(_collection.find(query, projection))

def fetch_raw_code_by_path(file_path):
    """Fetch raw_code for a specific file_path."""
    query = {"file_path": file_path, "type": "CodeFile.class"}
    projection = {"_id": 0, "raw_code": 1}
    return _collection.find_one(query, projection)

def fetch_codefile_doc_by_path(file_path):
    """Fetch raw_code for a specific file_path."""
    query = {"file_path": file_path, "type": "CodeFile.class"}
    projection = {
        "_id": 0,  # Exclude the _id field
        "file_path": 1,  # Include file_path
        "raw_code": 1,  # Include raw_code
        "cleaned_code": 1,  # Include cleaned_code
        "docstrings": 1,  # Include docstrings
        "entities": 1,  # Include entities
        "function_calls": 1,  # Include function_calls
        "imports": 1,  # Include imports
        "global_variables": 1,  # Include global_variables
        "embedding_ids": 1,  # Include embedding_ids
        "type": 1,  # Include type
    }
    return _collection.find_one(query, projection)

def fetch_codefile_doc_by_embedding_id(embedding_id):
    """Fetch raw_code and other fields for a specific embedding id."""
    # Convert embedding_id to a native Python int
    embedding_id = int(embedding_id)
    
    query = {"embedding_ids": embedding_id, "type": "CodeFile.class"}
    projection = {
        "_id": 0,  # Exclude the _id field
        "file_path": 1,  # Include file_path
        "raw_code": 1,  # Include raw_code
        "cleaned_code": 1,  # Include cleaned_code
        "docstrings": 1,  # Include docstrings
        "entities": 1,  # Include entities
        "function_calls": 1,  # Include function_calls
        "imports": 1,  # Include imports
        "global_variables": 1,  # Include global_variables
        "embedding_ids": 1,  # Include embedding_ids
        "type": 1,  # Include type
    }
    return _collection.find_one(query, projection)

# Document Operations (new additions)
def insert_document_file(document_content):
    """Insert a document file into the collection."""
    return _collection.insert_one(document_content)

def fetch_all_documents():
    """Fetch all documents of type 'DocumentationFile.class'."""
    query = {"type": "DocumentationFile.class"}
    projection = {
        "_id": 0,
        "file_path": 1,
        "sections": 1,
        "raw_content": 1,
        "cleaned_content": 1,
        "api_references": 1,
        "embedding_ids": 1,
        "type": 1
    }
    return list(_collection.find(query, projection))

def fetch_document_by_path(file_path):
    """Fetch document data for a specific file_path."""
    query = {"file_path": file_path, "type": "DocumentationFile.class"}
    projection = {
        "_id": 0,
        "file_path": 1,
        "sections": 1,
        "raw_content": 1,
        "cleaned_content": 1,
        "api_references": 1,
        "embedding_ids": 1,
        "type": 1
    }
    return _collection.find_one(query, projection)

def fetch_document_doc_by_embedding_id(embedding_id):
    """Fetch document for a specific embedding id."""
    # Convert embedding_id to a native Python int
    embedding_id = int(embedding_id)
    
    query = {"embedding_id": embedding_id, "type": "DocumentationFile.class"}
    projection = {
        "_id": 0,
        "file_path": 1,
        "sections": 1,
        "raw_content": 1,
        "cleaned_content": 1,
        "api_references": 1,
        "embedding_ids": 1,
        "type": 1
    }
    return _collection.find_one(query, projection)

def insert_metadata(metadata_list):
    if not isinstance(metadata_list, list):
        metadata_list = [metadata_list]

    for entry in metadata_list:
        if not all(k in entry for k in ("function_name", "file_path", "api_reference")):
            raise ValueError(f"Invalid metadata schema: {entry}")

    logger.info(f"Inserting {len(metadata_list)} metadata entries.")
    return _collection.insert_many(metadata_list)

def fetch_metadata(query_filter=None):
    query_filter = query_filter or {}
    logger.info(f"Fetching metadata with filter: {query_filter}")
    cursor = _collection.find(query_filter)
    return list(cursor)

def fetch_one_metadata(query_filter=None):
    query_filter = query_filter or {}
    return _collection.find_one(query_filter)

def update_metadata(query_filter, update_values, multiple=False):
    if multiple:
        logger.info(f"Updating multiple metadata entries with filter: {query_filter}")
        return _collection.update_many(query_filter, {"$set": update_values})
    else:
        logger.info(f"Updating one metadata entry with filter: {query_filter}")
        return _collection.update_one(query_filter, {"$set": update_values})

def delete_metadata(query_filter, multiple=False):
    if multiple:
        logger.info(f"Deleting multiple metadata entries with filter: {query_filter}")
        return _collection.delete_many(query_filter)
    else:
        logger.info(f"Deleting one metadata entry with filter: {query_filter}")
        return _collection.delete_one(query_filter)

def count_metadata(query_filter=None):
    query_filter = query_filter or {}
    return _collection.count_documents(query_filter)

def clear_collection():
    logger.info("Clearing entire metadata collection.")
    return _collection.delete_many({})

def collection_exists():
    exists = _config["metadata_collection"] in _db.list_collection_names()
    logger.info(f"Collection exists: {exists}")
    return exists