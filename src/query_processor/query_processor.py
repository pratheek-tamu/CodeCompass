import os
import argparse
import json
import logging
import re
import requests
import google.generativeai as genai
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.indexers.codefile_indexer import CodeBERTIndexer
from src.utils.graphdb_utils import get_dependencies, get_dependents, entity_exists
from src.retrievers.codefile_retriever import fetch_code_file_by_file_path

# Configure logging for debug information
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API with your API key from environment variables.
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if not gemini_api_key:
    logger.error("GEMINI_API_KEY environment variable is not set!")
    raise ValueError("Missing GEMINI_API_KEY environment variable.")
genai.configure(api_key=gemini_api_key)

def preprocess_query(query: str) -> str:
    """
    Preprocess the input query by trimming whitespace and removing non-ASCII characters.
    Additional normalization (e.g., lowercasing, spell-check) can be added as needed.
    """
    query = query.strip()
    query = query.encode("ascii", errors="ignore").decode()
    return query
    
def clean_response(response_text: str) -> str:
    """
    Removes markdown code fences (like ```json ... ```) from the response text.
    """
    if response_text.startswith("```json"):
        response_text = response_text[len("```json"):].strip()
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()
    return response_text

def call_gemini_api(prompt: str) -> str:
    """
    Calls the Gemini API using the google.generativeai package and returns the cleaned response text.
    The prompt should instruct Gemini to output JSON.
    
    Args:
        prompt (str): The prompt to send to Gemini.
    
    Returns:
        str: The generated text response from Gemini, or None if the response is empty.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        raw_text = response.text if response and response.text else ""
        if not raw_text.strip():
            logger.error("Received empty response from Gemini API for prompt: %s", prompt)
            return None
        cleaned_text = clean_response(raw_text)
        logger.info("Cleaned Gemini response: %s", cleaned_text)
        return cleaned_text
    except Exception as e:
        logger.error("Error calling Gemini API: %s", e)
        return None

def extract_entities_heuristic(query: str):
    """
    Fallback extraction using regex if the Gemini API call fails.
    Extracts function names (ending with '()') and modules/classes (capitalized words).
    """
    functions = re.findall(r'\b\w+\(\)', query)
    modules = re.findall(r'\b[A-Z][a-zA-Z0-9_]+\b', query)
    return functions, modules

def classify_query(query: str) -> str:
    """
    Heuristically classifies the query as 'code', 'documentation', or 'hybrid'.
    """
    lower_query = query.lower()
    if "documentation" in lower_query or "doc" in lower_query:
        return "documentation"
    elif "function" in lower_query or "module" in lower_query or "code" in lower_query:
        return "code"
    else:
        return "hybrid"

def extract_entity_names(json_file_path="data/code_indexer.metadata.json", useFunction=False):
    """
    Extracts entities of type 'function' or 'class' from the CodeFile Indexer results
    or a JSON metadata file, and returns them grouped by type.

    Args:
        json_file_path (str): The path to the JSON file to parse.
        useFunction (bool): Whether to use function-based input instead of reading from file.

    Returns:
        dict: A dictionary with keys as 'function' or 'class', and values as lists of names (str).
    """
    extracted = {"function": [], "class": []}

    if not useFunction:
        with open(json_file_path, 'r') as file:
            data = json.load(file)

    for item in data:
        if "entities" in item and "file_path" in item:
            for entity in item["entities"]:
                entity_type = entity.get("type")
                entity_name = entity.get("name")
                if entity_type in {"function", "class"} and entity_name:
                    extracted[entity_type].append(entity_name)

    return extracted

def get_extraction_from_gemini(query: str) -> dict:
    """
    Uses the Gemini API to extract entities and classify the query.
    This version includes additional context: the known function and class names
    extracted from the repository metadata. If the API call fails or the output is
    invalid, it falls back to heuristic extraction.
    
    Args:
        query (str): The preprocessed input query.
    
    Returns:
        dict: A dictionary with keys "functions", "modules", and "classification".
    """
    # Get the known entity names from the repository metadata
    extracted_names = extract_entity_names()
    context_json = json.dumps(extracted_names, indent=2)

    extraction_prompt = (
        f"Context: Below is a list of known entity names extracted from our code repository:\n"
        f"{context_json}\n\n"
        "Based on this context, process the following query. Extract the following information:\n"
        "- A list of function names mentioned in the query (only include names that are present in the context).\n"
        "- A list of class or module names mentioned in the query (only include names that are present in the context).\n"
        "- Classification: Indicate whether the query is code-related, documentation-related, or hybrid.\n\n"
        "Important: All valid function and class names are provided in the context above. Do not hallucinate "
        "or include any names that are not in the context. If the query mentions an entity not present in the context, "
        "do not include it in the output.\n\n"
        f"Query: \"{query}\"\n"
        "Respond in valid JSON format with double quotes for keys and values. "
        "The JSON should have keys: \"functions\", \"modules\", and \"classification\"."
    )

    response = call_gemini_api(extraction_prompt)
    if response is None:
        logger.warning("Gemini API call failed for extraction; using heuristic extraction.")
        functions, modules = extract_entities_heuristic(query)
        classification = classify_query(query)
        return {"functions": functions, "modules": modules, "classification": classification}
    
    try:
        data = json.loads(response)
    except json.decoder.JSONDecodeError as e:
        logger.warning("JSON decoding failed for extraction, attempting to fix quotes: %s", e)
        fixed_response = response.replace("'", "\"")
        try:
            data = json.loads(fixed_response)
        except Exception as e2:
            logger.error("Error processing Gemini extraction response after fixing quotes: %s", e2)
            functions, modules = extract_entities_heuristic(query)
            classification = classify_query(query)
            return {"functions": functions, "modules": modules, "classification": classification}
    
    if not all(key in data for key in ["functions", "modules", "classification"]):
        logger.error("Missing keys in Gemini extraction response. Response was: %s", data)
        functions, modules = extract_entities_heuristic(query)
        classification = classify_query(query)
        return {"functions": functions, "modules": modules, "classification": classification}
    
    # If the query is code-related or hybrid but no valid entities were found, terminate with an error.
    if not data.get("functions") and not data.get("modules"):
        logger.error("Invalid query: The query does not reference any known function or class names from our context.")
        raise SystemExit("Invalid query: The query does not reference any known function or class names from our context.")
    
    return data

def fallback_reformulated_queries(extracted_data: dict) -> dict:
    """
    Fallback method to generate reformulated queries using simple templates based on heuristic data.
    
    Args:
        extracted_data (dict): Contains heuristic data (functions, modules).
    
    Returns:
        dict: A dictionary with template-based reformulated queries.
    """
    modules = extracted_data.get("modules", ["ModuleA", "ModuleB"])
    functions = extracted_data.get("functions", ["processData()"])
    graphdb_query = f"Find all function calls and dependencies between modules: {', '.join(modules)}."
    metadata_query = f"Retrieve file paths, API references, and documentation for modules: {', '.join(modules)}."
    faiss_query = f"Search for similar embeddings to functions: {', '.join(functions)}."
    documentation_query = f"Find all documentation entries mentioning modules: {', '.join(modules)}."
    return {
        "graphdb_query": graphdb_query,
        "metadata_query": metadata_query,
        "faiss_query": faiss_query,
        "documentation_query": documentation_query
    }

def get_reformulated_queries(query: str, extracted_data: dict) -> dict:
    """
    Uses the Gemini API to generate backend-specific reformulated queries based on the extracted data.
    Falls back to a template-based approach if the API call fails or the output is invalid.
    """
    reformulation_prompt = (
        f"Using the following extracted information:\n"
        f"Functions: {extracted_data.get('functions', [])}\n"
        f"Modules: {extracted_data.get('modules', [])}\n"
        f"Classification: {extracted_data.get('classification')}\n"
        "Generate a JSON output with the following keys:\n"
        "- graphdb_query: A query to retrieve relationships and dependencies in the code.\n"
        "- metadata_query: A query to retrieve metadata and documentation references.\n"
        "- faiss_query: A query to search for similar code patterns or embeddings.\n"
        "- documentation_query: A query to retrieve documentation entries.\n"
        "Ensure the queries are tailored to the context of a codebase. "
        "Respond in valid JSON format with double quotes for keys and values.\n"
        f"Original Query: \"{query}\"."
    )
    response = call_gemini_api(reformulation_prompt)
    if response is None:
        logger.warning("Gemini API call failed for reformulation; using fallback templates.")
        return fallback_reformulated_queries(extracted_data)
    
    try:
        data = json.loads(response)
    except json.decoder.JSONDecodeError as e:
        logger.warning("JSON decoding failed during reformulation, attempting to fix quotes: %s", e)
        fixed_response = response.replace("'", "\"")
        try:
            data = json.loads(fixed_response)
        except Exception as e2:
            logger.error("Error processing Gemini reformulation response after fixing quotes: %s", e2)
            return fallback_reformulated_queries(extracted_data)
    
    if not all(key in data for key in ["graphdb_query", "metadata_query", "faiss_query", "documentation_query"]):
        logger.error("Missing keys in Gemini reformulation response. Response was: %s", data)
        return fallback_reformulated_queries(extracted_data)
    
    return data

def fallback_reformulated_queries(extracted_data: dict) -> dict:
    """
    Fallback method to generate reformulated queries using simple templates based on heuristic data.
    
    Args:
        extracted_data (dict): Contains heuristic data (functions, modules).
    Returns:
        dict: A dictionary with template-based reformulated queries.
    """
    modules = extracted_data.get("modules", ["ModuleA", "ModuleB"])
    functions = extracted_data.get("functions", ["processData()"])
    graphdb_query = f"Find all function calls and dependencies between modules: {', '.join(modules)}."
    metadata_query = f"Retrieve file paths, API references, and documentation for modules: {', '.join(modules)}."
    faiss_query = f"Search for similar embeddings to functions: {', '.join(functions)}."
    documentation_query = f"Find all documentation entries mentioning modules: {', '.join(modules)}."
    return {
        "graphdb_query": graphdb_query,
        "metadata_query": metadata_query,
        "faiss_query": faiss_query,
        "documentation_query": documentation_query
    }

def build_faiss_query_from_graph(node_name):
    deps = get_dependencies(node_name)  # dependencies
    users = get_dependents(node_name)   # dependents

    query_parts = [f"Node: {node_name}"]

    if deps:
        query_parts.append(f"Depends on: {', '.join(deps)}")
    if users:
        query_parts.append(f"Used by: {', '.join(users)}")

    return ". ".join(query_parts)

def process_query(query: str) -> dict:
    """
    Full processing pipeline:
    1. Preprocess the query.
    2. Extract entities and classification using Gemini API (with heuristic fallback).
    3. Reformulate the query for backend systems using Gemini API (with fallback).
    
    Args:
        query (str): The raw input query.
    Returns:
        dict: A dictionary with the final reformulated queries.
    """
    preprocessed_query = preprocess_query(query)
    extracted_data = get_extraction_from_gemini(preprocessed_query)
    if extracted_data['classification']:
        query_classification = extracted_data['classification']
        if query_classification == "code-related":
            print("Call graphdb and faiss db")
            # use graphdb utils to fetch information from graphdb
            nodes_to_search = []
            nodes_to_search.extend(extracted_data['functions'])
            nodes_to_search.extend(extracted_data['modules'])

            nodes_to_search = list(filter(lambda x: entity_exists(x), nodes_to_search))

            print("Extracted and filtered nodes from User's Initial Query")
            
            # use the nodes and extract dependent nodes from graphdb (networkx)
            faiss_query = dict()
            for i in nodes_to_search:
                faiss_query[i] = build_faiss_query_from_graph(i)
            
            # print(f"FAISS Query built. {faiss_query}")
            print(f"FAISS Query built.")
            
            # once we have each node with its deps, query faiss to extract code for context
            indexer = CodeBERTIndexer()
            context_for_llm = ""
            for node, query_code in faiss_query.items():
                result_paths, distances = indexer.search_similar(query_code)
                # print(f"Results: {result_paths}")
                codefile = fetch_code_file_by_file_path(result_paths[0])
                # print(f"Found similar code in the following files: {result_paths}")
                # print(f"Distances: {distances}")
                context_for_llm += f"\nNode from User's Query:{node}\n\nRaw Code: {codefile.raw_code}\n\n"
            
            print("LLM Context ready.")

            # Using code, generate answer for the original query
            extraction_prompt = (
                f"Context: The user has totally seeked information about {len(nodes_to_search)} modules and functions. The below information contains the node of interest from user's query and the raw code of the file it is associated with:\n"
                f"{context_for_llm}\n\n"
                f"Based on the above context, answer the user's question in an accurate way.\n"
            )
            response = call_gemini_api(extraction_prompt)
            print("Final Response: ", response)

        elif query_classification == "documentation-related":
            print("Call FAISS and metadata-db")
        elif query_classification == "hybrid":
            print("Call FAISS, graphdb, and metadata db")
        else:
            print("Invalid classification")
    else:
        print("Error")

    # reformulated_queries = get_reformulated_queries(preprocessed_query, extracted_data)
    # return reformulated_queries

def main():
    parser = argparse.ArgumentParser(
        description="Robust CLI-based Query Processor Module"
    )

    parser.add_argument("query", type=str, help="Input query string")
    args = parser.parse_args()
    
    print(process_query(args.query))

    # old for reformulation
    # results = process_query(args.query)
    # print(json.dumps(results, indent=4))

if __name__ == "__main__":
    main()
