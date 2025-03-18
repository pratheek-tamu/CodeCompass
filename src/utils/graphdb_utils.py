import networkx as nx
import pickle
import os
from utils.logging_utils import setup_logger
from utils.config_loader import load_config

# Setup Logging
logger = setup_logger()

# Load configuration once when module is imported
_config = load_config()["graphdb"]
_graph_storage_path = _config["graph_storage_path"]

_graph = None

def _get_graph():
    global _graph
    if _graph is None:
        _graph = load_graph()
    return _graph

def create_graph():
    logger.info("Creating a new GraphDB (NetworkX) instance.")
    return nx.DiGraph()

def load_graph():
    if os.path.exists(_graph_storage_path):
        logger.info(f"Loading GraphDB from {_graph_storage_path}")
        with open(_graph_storage_path, "rb") as f:
            return pickle.load(f)
    
    logger.info("No GraphDB found. Creating a new one.")
    graph = create_graph()
    save_graph(graph)
    return graph

def save_graph(graph):
    os.makedirs(os.path.dirname(_graph_storage_path), exist_ok=True)
    with open(_graph_storage_path, "wb") as f:
        pickle.dump(graph, f)
    logger.info(f"GraphDB saved to {_graph_storage_path}")

def add_dependency(source_entity, target_entity):
    graph = _get_graph()
    graph.add_edge(source_entity, target_entity)
    save_graph(graph)

def get_dependencies(entity_name):
    graph = _get_graph()
    return list(graph.successors(entity_name))

def get_dependents(entity_name):
    graph = _get_graph()
    return list(graph.predecessors(entity_name))

def entity_exists(entity_name):
    graph = _get_graph()
    return graph.has_node(entity_name)

def clear_graph():
    global _graph
    _graph = create_graph()
    save_graph(_graph)
    logger.info("GraphDB cleared.")

def get_all_entities():
    graph = _get_graph()
    return list(graph.nodes())

def get_all_dependencies():
    graph = _get_graph()
    return list(graph.edges())
