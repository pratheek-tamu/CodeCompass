import faiss
import numpy as np
import os
from .logging_utils import setup_logger
from .config_loader import load_config

# Setup Logging
logger = setup_logger()

# Load configuration once when module is imported
_config = load_config()["faiss"]
_index_path = _config["index_path"]
_embedding_dimension = _config["embedding_dimension"]

_faiss_index = None

def _get_faiss_index():
    global _faiss_index
    if _faiss_index is None:
        _faiss_index = load_faiss_index()
    return _faiss_index

def create_faiss_index():
    logger.info("Creating a new FAISS index.")
    return faiss.IndexFlatL2(_embedding_dimension)

def load_faiss_index():
    if os.path.exists(_index_path):
        logger.info(f"Loading FAISS index from {_index_path}")
        return faiss.read_index(_index_path)
    
    logger.info("No FAISS index found. Creating a new one.")
    index = create_faiss_index()
    save_faiss_index(index)
    return index

def save_faiss_index(index):
    os.makedirs(os.path.dirname(_index_path), exist_ok=True)
    faiss.write_index(index, _index_path)
    logger.info(f"FAISS index saved to {_index_path}")

def add_embeddings_to_index(embeddings):
    if not isinstance(embeddings, np.ndarray):
        raise ValueError("Embeddings must be a numpy array.")
    
    if embeddings.ndim != 2 or embeddings.shape[1] != _embedding_dimension:
        raise ValueError(f"Embeddings must have shape (n, {_embedding_dimension}).")

    index = _get_faiss_index()
    index.add(embeddings)
    save_faiss_index(index)

def search_similar_vectors(query_embedding, k=5):
    if not isinstance(query_embedding, np.ndarray):
        raise ValueError("Query embedding must be a numpy array.")
    
    if query_embedding.shape != (_embedding_dimension,):
        raise ValueError(f"Query embedding must have shape ({_embedding_dimension},).")

    query_embedding = np.expand_dims(query_embedding, axis=0)
    index = _get_faiss_index()
    
    distances, indices = index.search(query_embedding, k)
    return indices[0], distances[0]

class FAISSManager:
    def __init__(self):
        self.index = _get_faiss_index()
        
    def add_embeddings(self, embeddings):
        if not isinstance(embeddings, np.ndarray):
            raise ValueError("Embeddings must be a numpy array.")
        self.index.add(embeddings)
        save_faiss_index(self.index)
        
    def search(self, query_embedding, k=5):
        query_embedding = np.expand_dims(query_embedding, axis=0)
        distances, indices = self.index.search(query_embedding, k)
        return indices[0], distances[0]