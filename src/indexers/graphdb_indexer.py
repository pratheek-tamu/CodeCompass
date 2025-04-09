from src.utils.graphdb_utils import _get_graph, save_graph
from src.utils.logging_utils import log_info, setup_logger

logger = setup_logger()

def add_caller_callee_relations(code_file):
    """
    Takes a single CodeFile object and updates the graph with caller-callee relationships.
    """
    graph = _get_graph()
    
    for function_call in code_file.function_calls:
        caller = function_call.caller
        callee = function_call.callee

        # Ensure both caller and callee exist in the graph
        if not graph.has_node(caller):
            graph.add_node(caller, file_path=function_call.file_path)
        graph.nodes[caller]["file_path"] = function_call.file_path
        if not graph.has_node(callee):
            graph.add_node(callee, file_path=function_call.file_path)
        graph.nodes[callee]["file_path"] = function_call.file_path
        
        # Add dependency (caller → callee)
        graph.add_edge(caller, callee, line_number=function_call.line_number)

    save_graph(graph)
    log_info(logger, f"Updated GraphDB with caller-callee relationships from {code_file.file_path}.")

