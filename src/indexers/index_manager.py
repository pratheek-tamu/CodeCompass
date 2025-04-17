from src.indexers.codefile_indexer import CodeBERTIndexer
from src.indexers.docfile_indexer import DocumentIndexer

class IndexManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.code_indexer = CodeBERTIndexer()
            cls._instance.doc_indexer = DocumentIndexer()
        return cls._instance

    def get_code_indexer(self):
        return self._instance.code_indexer

    def get_doc_indexer(self):
        return self._instance.doc_indexer
