import torch
from transformers import RobertaModel, RobertaTokenizer
import numpy as np

class CodeBERTIndexer:
    def __init__(self, model_name="microsoft/codebert-base", embedding_dim=768):
        # Initialize model and tokenizer
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

    def add_code_to_index(self, code: str, faiss_manager):
        """Encodes the code and adds its embedding to the FAISS index."""
        embedding = self.encode_code(code)
        faiss_manager.add_embeddings(np.array([embedding]))  # Add to FAISS index
        self.id_count += 1
        return self.id_count
