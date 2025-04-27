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

    def set_index_value(self, updated_id_count: int):
        self.id_count = updated_id_count

    def encode_code(self, code: str):
        """Encodes code using CodeBERT to produce a vector representation."""
        inputs = self.tokenizer(code, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).cpu().numpy().flatten()
    
    def encode_code_by_chunks(self, code: str, chunk_size=512):
        """Encodes code in chunks to get multiple embeddings per file."""
        tokens = self.tokenizer.tokenize(code)
        chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]

        embeddings = []
        for chunk in chunks:
            inputs = self.tokenizer(
                chunk,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512,
                is_split_into_words=True,
            )

            with torch.no_grad():
                outputs = self.model(**inputs)
                chunk_embedding = outputs.last_hidden_state.mean(dim=1)
                embeddings.append(chunk_embedding.squeeze(0).cpu().numpy())

        return embeddings

    def add_code_to_index(self, code: str, faiss_manager):
        """Encodes the code and adds its embedding to the FAISS index."""
        embedding = self.encode_code(code)
        faiss_manager.add_embeddings(np.array([embedding]))  # Add to FAISS index
        self.id_count += 1
        return self.id_count
    
    def add_code_to_index_by_chunks(self, code: str, faiss_manager):
        """Encodes the code and adds its embedding to the FAISS index."""
        embeddings = self.encode_code_by_chunks(code)
        embedding_ids = []
        for embedding in embeddings:
            faiss_manager.add_embeddings(np.array([embedding]))  # Add to FAISS index
            print("Debugging", self.id_count)
            self.id_count += 1
            embedding_ids.append(self.id_count)
        print("id_count: ", self.id_count)
        return embedding_ids, self.id_count
