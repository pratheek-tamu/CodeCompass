from pymongo import MongoClient
from utils.logging_utils import setup_logger
from utils.config_loader import load_config

# Setup Logging
logger = setup_logger()

# Load configuration once when module is imported
_config = load_config()["mongodb"]
_client = MongoClient(_config["uri"], maxPoolSize=50)
_db = _client[_config["database"]]
_collection = _db[_config["metadata_collection"]]

def get_collection():
    return _collection

def insert_metadata(metadata_list):
    if not isinstance(metadata_list, list):
        metadata_list = [metadata_list]

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
