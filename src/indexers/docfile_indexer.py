import torch
from transformers import AutoModel, AutoTokenizer
import numpy as np

class DocumentIndexer:
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", embedding_dim=768):
        # Initialize model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.embedding_dim = embedding_dim
        self.id_count = -1  # Store document IDs corresponding to FAISS index entries

    def encode_document(self, document: str):
        """Encodes document text to produce a vector representation."""
        inputs = self.tokenizer(document, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).cpu().numpy().flatten()

    def add_document_to_index(self, document: str, faiss_manager):
        """Encodes the document and adds its embedding to the FAISS index."""
        embedding = self.encode_document(document)
        faiss_manager.add_embeddings(np.array([embedding]))  # Add to FAISS index
        self.id_count += 1
        return self.id_count