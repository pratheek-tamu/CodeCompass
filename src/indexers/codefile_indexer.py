import torch
from transformers import RobertaModel, RobertaTokenizer
import numpy as np
from src.utils.embedding_utils import add_embeddings_to_index, search_similar_vectors 

class CodeBERTIndexer:
    def __init__(self, model_name="microsoft/codebert-base", embedding_dim=768):
        # Initialize model and tokenizer (same as before)
        self.tokenizer = RobertaTokenizer.from_pretrained(model_name)
        self.model = RobertaModel.from_pretrained(model_name)
        self.embedding_dim = embedding_dim
        self.id_count = -1  # This will store file paths corresponding to FAISS index entries.

    def encode_code(self, code: str):
        """Encodes code using CodeBERT to produce a vector representation."""
        inputs = self.tokenizer(code, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).cpu().numpy().flatten()

    def add_code_to_index(self, code: str):
        """Encodes the code and adds its embedding to the FAISS index."""
        embedding = self.encode_code(code)
        add_embeddings_to_index(np.array([embedding]))  # Add to FAISS index
        self.id_count += 1
        return self.id_count

    def search_similar(self, query_code: str, k=5):
        """Searches for similar code snippets in the FAISS index."""
        query_embedding = self.encode_code(query_code)
        indices, distances = search_similar_vectors(query_embedding, k)
        return indices, distances
