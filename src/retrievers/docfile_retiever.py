from typing import List
from src.ingestion.data_models import DocumentationFile
from src.utils.mongodb_utils import fetch_document_by_path, fetch_all_documents, fetch_document_doc_by_embedding_id
from src.utils.logging_utils import log_error

def fetch_document_by_file_path(file_path: str) -> DocumentationFile:
    """
    Data transfer object (DTO) transformer from DB docs
    """
    document = fetch_document_by_path(file_path)
    
    if not document:
        log_error(f"No document found for file_path: {file_path}")
        return None

    return DocumentationFile(
        file_path=document.get('file_path'),
        sections=document.get('sections', []),
        raw_content=document.get('raw_content', ''),
        cleaned_content=document.get('cleaned_content'),
        api_references=document.get('api_references', ''),
        embedding_id=document.get('embedding_id'),
        type=document.get('type', 'DocumentationFile.class')
    )

def fetch_document_by_embedding_id(embedding_id: int) -> DocumentationFile:
    """
    Data transfer object (DTO) transformer from DB docs
    """
    document = fetch_document_doc_by_embedding_id(embedding_id)
    
    if not document:
        log_error(f"No document found for embedding_id: {embedding_id}")
        return None
    
    return DocumentationFile(
        file_path=document.get('file_path'),
        sections=document.get('sections', []),
        raw_content=document.get('raw_content', ''),
        cleaned_content=document.get('cleaned_content'),
        api_references=document.get('api_references', []),
        embedding_id=document.get('embedding_id'),
        type=document.get('type', 'DocumentationFile.class')
    )

def fetch_all_documents_from_db() -> List[DocumentationFile]:
    """
    Data transfer object (DTO) transformer from DB docs
    """
    documents = fetch_all_documents()
    
    document_files = []
    for document in documents:
        document_files.append(DocumentationFile(
            file_path=document.get('file_path'),
            sections=document.get('sections', []),
            raw_content=document.get('raw_content', ''),
            cleaned_content=document.get('cleaned_content'),
            api_references=document.get('api_references', ''),
            embedding_id=document.get('embedding_id'),
            type=document.get('type', 'DocumentationFile.class')
        ))
    
    return document_files