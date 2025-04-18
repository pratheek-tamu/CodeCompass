import os
import json
import logging
import re
import sys
import google.generativeai as genai

from src.indexers.index_manager import IndexManager
from src.utils.graphdb_utils import get_dependencies, entity_exists
from src.utils.embedding_utils import FAISSManager
from src.retrievers.codefile_retriever import fetch_code_file_by_embedding_id, fetch_all_code_files
from src.retrievers.docfile_retiever import fetch_document_by_embedding_id

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API Configuration
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if not gemini_api_key:
    logger.error("GEMINI_API_KEY environment variable is not set!")
    raise ValueError("Missing GEMINI_API_KEY environment variable.")
genai.configure(api_key=gemini_api_key)

# Initialize IndexManager and FAISSManager
index_manager = IndexManager()
code_indexer = index_manager.get_code_indexer()
doc_indexer = index_manager.get_doc_indexer()
faiss_manager = FAISSManager() # Assumes FAISSManager is attached to CodeBERTIndexer

def preprocess_query(query: str) -> str:
    """
    Preprocess the input query by trimming whitespace and removing non-ASCII characters.
    Additional normalization (e.g., lowercasing, spell-check) can be added as needed.
    """
    return query.strip().encode("ascii", errors="ignore").decode()

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
        return clean_response(raw_text)
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
    Heuristically classifies the query as 'code', or 'documentation'.
    """
    q = query.lower()
    if "documentation" in q or "doc" in q:
        return "documentation"
    elif "function" in q or "module" in q or "code" in q:
        return "code"
    return "Invalid"

def extract_entity_names(code_files):
    """
    Extracts entities of type 'function' or 'class' from the CodeFile Indexer results,
    and returns them grouped by type.

    Args:
        code_files (list): Contains objects to be parsed.

    Returns:
        dict: A dictionary with keys as 'function' or 'class', and values as lists of names (str).
    """
    extracted = {"function": [], "class": []}

    for code_file in code_files:
        entities = code_file.entities
        for entity in entities:
            if entity.type in {"function", "class"} and entity.name:
                extracted[entity.type].append(entity.name)
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
    extracted_names = extract_entity_names(fetch_all_code_files())
    context_json = json.dumps(extracted_names, indent=2)

    extraction_prompt = (
        "You are an assistant that classifies developer queries and extracts mentioned entities.\n\n"
        "You are given:\n"
        "- A context of known function and class names from a codebase (see below).\n"
        "- A user query that may refer to code, documentation, or both.\n\n"
        "Code Context:\n"
        f"{context_json}\n\n"
        "User Query:\n"
        f"\"{query}\"\n\n"
        "Your tasks:\n"
        "1. From the context, extract which function names are mentioned in the query.\n"
        "2. From the context, extract which class/module names are mentioned in the query.\n"
        "3. Classify the query as one of the following:\n"
        "   - \"code-related\" → focuses on implementation, debugging, performance, or how code works. Queries that are a mix of Code structure + Doc explanation can also be classified in this category\n"
        "   - \"documentation-related\" → focuses on usage, purpose, description, or explanations from docs.\n"
        "Important rules:\n"
        "- Do NOT invent names. Only use names from the Code Context.\n"
        "- Use \"code-related\" **if both code and documentation are relevant** in the query.\n"
        "- Return a valid JSON object with keys: \"functions\", \"modules\", and \"classification\".\n"
        "- Double quotes must be used in JSON keys and string values.\n\n"
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
    
    # If the query is code-related but no valid entities were found, terminate with an error.
    if data.get("classification") == "code-related" and not data.get("functions") and not data.get("modules"):
        logger.error("Invalid query: The query does not reference any known function or class names from our context.") 
        return {}
    
    return data

def build_faiss_query_from_graph(node_name):
    deps = get_dependencies(node_name)
    query_parts = [f"Node: {node_name}"]
    if deps:
        query_parts.append(f"Depends on: {', '.join(deps)}")

    return ". ".join(query_parts)

def get_context_for_code(nodes):
    if not nodes:
        print("No relevant functions or modules found.")
        return

    print(f"Nodes identified: {nodes}")
    faiss_queries = {node: build_faiss_query_from_graph(node) for node in nodes}
    context_parts = []

    for node, query_code in faiss_queries.items():
        embedding = code_indexer.encode_code(query_code)
        indices, _ = faiss_manager.search(embedding)
        if indices is None or len(indices) == 0:
            continue
        codefile = fetch_code_file_by_embedding_id(indices[0])
        context_parts.append(f"\nNode: {node}\n\nRaw Code:\n{codefile.raw_code}\n")
    print(codefile.file_path)
    if not context_parts:
        print("No code context retrieved.")
        return

    return context_parts

def get_context_for_document(query):
    embedding = doc_indexer.encode_document(query)
    indices, _ = faiss_manager.search(embedding)
    if indices is None or len(indices) == 0:
        print("No index. Embedding not found")
        return
    docfile = fetch_document_by_embedding_id(indices[0])
    return docfile.raw_content

def extract_documentation_related_response(query):
    document_context = get_context_for_document(query)    

    llm_context = (
        f"The user asked the following documentation-related query:\n\"{query}\"\n\n"
        "Below is the relevant documentation extracted from the codebase:\n"
        f"{'-'*80}\n" +
        "\n".join(document_context) +
        f"\n{'-'*80}\n"
        "### Instructions:\n"
        "- Use the documentation above to answer the query.\n"
        "- Be concise and accurate.\n"
        "- If the documentation does not directly address the query, say so explicitly.\n"
    )

    response = call_gemini_api(llm_context)
    return response

def extract_code_related_response(nodes, query):
    code_context = get_context_for_code2(nodes)
    document_context = get_context_for_document(query)  

    llm_context = (
        f"The user has asked the following query related to code entities: {query}\n\n"
        f"## Code Entities Mentioned ({len(nodes)} total): {nodes}\n"
        f"Below is the raw code relevant to these nodes:\n"
        f"{'-'*80}\n" +
        "\n".join(code_context) +
        f"\n{'-'*80}\n"
        "In addition to the code, here is the documentation that might relate to the user's question.\n"
        "Use this documentation **only if** it helps clarify how the mentioned code entities work, are used, or are described in the broader system:\n"
        f"{'-'*80}\n" +
        "\n".join(document_context) +
        f"\n{'-'*80}\n"
        "### Instructions:\n"
        "- Focus primarily on answering based on the code logic, structure, and functionality.\n"
        "- Use the documentation only if it enhances the answer about the code entities.\n"
        "- If the documentation does not clearly relate to the mentioned code entities, **ignore it**.\n"
        "- Provide a clear and technically grounded explanation.\n"
    )

    response = call_gemini_api(llm_context)
    return response

def process_query(query: str) -> None:
    """
    Processes a user query by classifying and extracting relevant code/documentation context,
    and prints the final LLM response.
    """
    query = preprocess_query(query)
    extracted_data = get_extraction_from_gemini(query)
    classification = extracted_data.get("classification")

    if classification == "code-related":
        print("Classification: Code-related")
        nodes = list(filter(entity_exists, extracted_data.get("functions", []) + extracted_data.get("modules", [])))
        response = extract_code_related_response(nodes, query)
        print("Final Response:\n", response)

    elif classification == "documentation-related":
        print("Classification: Documentation-related")
        response = extract_documentation_related_response(query)
        print("Final Response:\n", response)
    else:
        print("Invalid classification")

def interactive_query_loop():
    print("Welcome to CodeCompass Query System! Type your query below, or type 'exit' to quit.")
    while True:
        try:
            query = input("\n> ").strip()
            if query.lower() in {"exit", "quit"}:
                print("Exiting. Thank you!")
                break
            process_query(query)
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    interactive_query_loop()
