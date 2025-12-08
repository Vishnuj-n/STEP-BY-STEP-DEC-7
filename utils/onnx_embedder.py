"""
ONNX-based embedding module for nomic-embed-text-v1.5.
Uses local ONNX model (./onxx/model_int8.onnx) instead of PyTorch.
"""

import streamlit as st
import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np
import os

class OnnxEmbedder:
    """Embed text using ONNX Runtime with nomic-embed-text-v1.5 model."""
    
    def __init__(self, model_path="onnx/model_int8.onnx"):
        """
        Initialize ONNX embedder with local model.
        
        Args:
            model_path (str): Path to ONNX model file (default: ./onnx/model_int8.onnx)
        """
        self.model_path = model_path
        self.tokenizer = None
        self.session = None
        self._initialize()
    
    def _initialize(self):
        """Initialize tokenizer and ONNX session."""
        try:
            # Load tokenizer
            print("Loading tokenizer for nomic-embed-text-v1.5...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                "nomic-ai/nomic-embed-text-v1.5",
                trust_remote_code=True
            )
            
            # Check if model exists
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"ONNX model not found at {self.model_path}\n"
                    f"Expected location: {os.path.abspath(self.model_path)}\n"
                    f"Please ensure you have placed the ONNX model there."
                )
            
            # Load ONNX session
            print(f"Loading ONNX model from {self.model_path}...")
            self.session = ort.InferenceSession(
                self.model_path,
                providers=["CPUExecutionProvider"]
            )
            print("✅ ONNX embedder initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing ONNX embedder: {e}")
            raise
    
    def embed(self, texts, prefix="search_document:"):
        """
        Embed texts using ONNX model.
        
        Args:
            texts (str or list): Text(s) to embed
            prefix (str): Prefix to add to texts ("search_document:" or "search_query:")
        
        Returns:
            np.ndarray: L2-normalized embeddings (shape: (n_texts, 768))
        """
        if self.session is None or self.tokenizer is None:
            raise RuntimeError("Embedder not initialized. Check ONNX model path.")
        
        # Handle single string input
        if isinstance(texts, str):
            texts = [texts]
        
        # Add prefix to all texts
        prefixed_texts = [f"{prefix} {text}" for text in texts]
        
        # Tokenize
        encoded = self.tokenizer(
            prefixed_texts,
            padding=True,
            truncation=True,
            return_tensors="np",
            max_length=8192
        )
        
        # Run inference
        input_ids = encoded["input_ids"].astype(np.int64)
        attention_mask = encoded["attention_mask"].astype(np.int64)
        
        # Check if model expects token_type_ids
        input_names = [inp.name for inp in self.session.get_inputs()]
        onnx_inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }
        
        # Add token_type_ids if required by the model
        if "token_type_ids" in input_names:
            token_type_ids = np.zeros_like(input_ids, dtype=np.int64)
            onnx_inputs["token_type_ids"] = token_type_ids
        
        embeddings = self.session.run(None, onnx_inputs)[0]
        
        # Check embedding shape and extract sentence embedding if needed
        # ONNX models sometimes return (batch, seq_len, hidden_dim) instead of (batch, hidden_dim)
        if len(embeddings.shape) == 3:
            # Take the [CLS] token (first token) as the sentence embedding
            embeddings = embeddings[:, 0, :]
        
        # L2 normalization
        embeddings = embeddings.astype(np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-12)
        
        return embeddings
    
    def embed_query(self, query):
        """
        Embed a query using search_query prefix.
        
        Args:
            query (str): Query text to embed
        
        Returns:
            np.ndarray: L2-normalized embedding (shape: (1, 768))
        """
        return self.embed([query], prefix="search_query:")[0]
    
    def embed_documents(self, documents):
        """
        Embed documents using search_document prefix.
        
        Args:
            documents (list): List of document texts to embed
        
        Returns:
            np.ndarray: L2-normalized embeddings (shape: (n_docs, 768))
        """
        return self.embed(documents, prefix="search_document:")


@st.cache_resource
def get_embedder():
    """Get or create cached embedder instance. Ensures model is loaded only once."""
    return OnnxEmbedder()

def embed_texts(texts, prefix="search_document:"):
    """
    Convenience function to embed texts.
    
    Args:
        texts (str or list): Text(s) to embed
        prefix (str): Prefix to add ("search_document:" or "search_query:")
    
    Returns:
        np.ndarray: L2-normalized embeddings
    """
    embedder = get_embedder()
    return embedder.embed(texts, prefix=prefix)

def embed_query(query):
    """
    Convenience function to embed a query.
    
    Args:
        query (str): Query text
    
    Returns:
        np.ndarray: L2-normalized embedding (shape: (768,))
    """
    embedder = get_embedder()
    return embedder.embed_query(query)

def embed_documents(documents):
    """
    Convenience function to embed documents.
    
    Args:
        documents (list): List of document texts
    
    Returns:
        np.ndarray: L2-normalized embeddings
    """
    embedder = get_embedder()
    return embedder.embed_documents(documents)
