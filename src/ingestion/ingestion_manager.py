from ingestion.file_crawler import crawl_files
from ingestion.code_parser import parse_code_file
from ingestion.doc_parser import parse_doc_file
from ingestion.data_models import IngestedData
from utils.logging_utils import setup_logger, log_info, log_warning

logger = setup_logger()

class IngestionManager:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.parsers = {
            ".py": parse_code_file,
            ".md": parse_doc_file
        }

    def ingest(self):
        """
        Orchestrates the ingestion process by crawling files, parsing them, 
        and returning structured data models.
        """
        files = crawl_files(self.root_dir)
        ingested_data = IngestedData()

        for file in files:
            try:
                # Determine parser based on file extension
                extension = file.split(".")[-1]
                parser = self.parsers.get(f".{extension}")

                if parser:
                    parsed_data = parser(file)
                    if isinstance(parsed_data, IngestedData.CodeFile):
                        ingested_data.code_files.append(parsed_data)
                    elif isinstance(parsed_data, IngestedData.DocumentationFile):
                        ingested_data.documentation_files.append(parsed_data)
                else:
                    log_warning(logger, f"No parser registered for file type: {file}")
            except Exception as e:
                log_warning(logger, f"Failed to parse {file}: {e}")

        log_info(f"Ingested {len(ingested_data.code_files)} code files and "
                    f"{len(ingested_data.documentation_files)} documentation files.")
        return ingested_data
