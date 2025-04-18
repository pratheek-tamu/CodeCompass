from typing import List
from src.ingestion.data_models import CodeFile, CodeEntity, FunctionCall
from src.utils.mongodb_utils import fetch_raw_code_by_path, fetch_all_raw_code, fetch_codefile_doc_by_embedding_id
from src.utils.logging_utils import log_error
from dataclasses import asdict

# Assuming your MongoDB setup and logging is already done

def fetch_code_file_by_file_path(file_path: str) -> CodeFile:
    """
    Data transfer object (DTO) transformer form DB docs
    """
    document = fetch_raw_code_by_path(file_path)
    
    if not document:
        log_error(f"No document found for file_path: {file_path}")
        return None

    entities = [CodeEntity(**entity) for entity in document.get('entities', [])]
    function_calls = [FunctionCall(**fc) for fc in document.get('function_calls', [])]
    
    return CodeFile(
        file_path=document.get('file_path'),
        entities=entities,
        raw_code=document.get('raw_code'),
        cleaned_code=document.get('cleaned_code'),
        docstrings=document.get('docstrings', []),
        function_calls=function_calls,
        imports=document.get('imports', []),
        global_variables=document.get('global_variables', []),
        embedding_ids=document.get('embedding_ids', []),
        type=document.get('type', 'CodeFile.class')
    )

def fetch_code_file_by_embedding_id(embedding_id: int) -> CodeFile:
    """
    Data transfer object (DTO) transformer form DB docs
    """
    document = fetch_codefile_doc_by_embedding_id(embedding_id)
    
    if not document:
        log_error(f"No document found for embedding_id: {embedding_id}")
        return None
    
    entities = [CodeEntity(**entity) for entity in document.get('entities', [])]
    function_calls = [FunctionCall(**fc) for fc in document.get('function_calls', [])]
    
    return CodeFile(
        file_path=document.get('file_path'),
        entities=entities,
        raw_code=document.get('raw_code'),
        cleaned_code=document.get('cleaned_code'),
        docstrings=document.get('docstrings', []),
        function_calls=function_calls,
        imports=document.get('imports', []),
        global_variables=document.get('global_variables', []),
        embedding_ids=document.get('embedding_ids', []),
        type=document.get('type', 'CodeFile.class')
    )

def fetch_all_code_files() -> List[CodeFile]:
    """
    Data transfer object (DTO) transformer form DB docs
    """
    documents = fetch_all_raw_code()
    
    code_files = []
    for document in documents:
        entities = [CodeEntity(**entity) for entity in document.get('entities', [])]
        function_calls = [FunctionCall(**fc) for fc in document.get('function_calls', [])]
        
        code_files.append(CodeFile(
            file_path=document.get('file_path'),
            entities=entities,
            raw_code=document.get('raw_code'),
            cleaned_code=document.get('cleaned_code'),
            docstrings=document.get('docstrings', []),
            function_calls=function_calls,
            imports=document.get('imports', []),
            global_variables=document.get('global_variables', []),
            embedding_ids=document.get('embedding_ids', []),
            type=document.get('type', 'CodeFile.class')
        ))
    
    return code_files
