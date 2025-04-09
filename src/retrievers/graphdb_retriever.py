from src.utils.graphdb_utils import get_all_dependencies, get_dependencies, get_dependents, entity_exists, _get_graph, get_all_entities

def get_callees(function_name):
    return get_dependencies(function_name)  # Reusing existing function

def get_callers(function_name):
    return get_dependents(function_name)  # Reusing existing function

def function_exists(function_name):
    return entity_exists(function_name)  # Reusing existing function

def get_function_file(function_name):
    graph = _get_graph()
    if graph.has_node(function_name):
        return graph.nodes[function_name].get("file_path", None)
    return None

def get_call_line_number(caller, callee):
    graph = _get_graph()
    if graph.has_edge(caller, callee):
        return graph[caller][callee].get("line_number", None)
    return None

def get_all_functions():
    return get_all_entities()  # Reusing existing function

def get_all_call_relationships():
    return get_all_dependencies()  # Reusing existing function
