import os

from .file_crawler import crawl_files
from .code_parser import parse_code_file
from .doc_parser import parse_doc_file
from .data_models import CodeFile, IngestedData, DocumentationFile

from src.utils.logging_utils import setup_logger, log_info, log_warning
from src.utils.mongodb_utils import insert_code_file, insert_document_file
from src.utils.embedding_utils import FAISSManager

from src.indexers.index_manager import IndexManager
from src.indexers.graphdb_indexer import add_caller_callee_relations

logger = setup_logger()

class IngestionManager:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.parsers = {
            ".py": parse_code_file,
            ".md": parse_doc_file
        }
        
        index_manager = IndexManager()
        self.code_indexer = index_manager.get_code_indexer()
        self.doc_indexer = index_manager.get_doc_indexer() 
        
        self.faiss_manager = FAISSManager()

    def ingest(self):
        """
        Orchestrates the ingestion process by crawling files, parsing them, 
        and returning structured data models.
        """
        log_info(logger, f"File root: {self.root_dir}")
        files = crawl_files(self.root_dir)
        ingested_data = IngestedData()

        for file in files:
            try:
                # Determine parser based on file extension
                _, extension = os.path.splitext(file)
                parser = self.parsers.get(extension)

                if parser:
                    parsed_data = parser(file)
                    if isinstance(parsed_data, CodeFile):
                        code_file = parsed_data
                        embedding_id = self.code_indexer.add_code_to_index(code_file.raw_code, self.faiss_manager)
                        code_file.embedding_id = embedding_id
                        insert_code_file(code_file.to_dict())
                        add_caller_callee_relations(code_file)
                        ingested_data.code_files.append(code_file)
                    elif isinstance(parsed_data, DocumentationFile):
                        doc_file = parsed_data
                        embedding_id = self.doc_indexer.add_document_to_index(doc_file.raw_content, self.faiss_manager)
                        doc_file.embedding_id = embedding_id
                        insert_document_file(doc_file.to_dict())
                        ingested_data.documentation_files.append(doc_file)
                else:
                    log_warning(logger, f"No parser registered for file type: {file}")
            except Exception as e:
                log_warning(logger, f"Failed to parse {file}: {e}")

        log_info(logger, f"Ingested {len(ingested_data.code_files)} code files and "
                    f"{len(ingested_data.documentation_files)} documentation files.")
        return ingested_data