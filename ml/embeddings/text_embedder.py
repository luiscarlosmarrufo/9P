"""
Text embedding utilities using sentence-transformers
"""

import numpy as np
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
import torch
from sklearn.metrics.pairwise import cosine_similarity

from control.core.config import settings


class TextEmbedder:
    """Text embedding class using sentence-transformers"""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the text embedder"""
        self.model_name = model_name or settings.SENTENCE_TRANSFORMER_MODEL
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            print(f"Loaded embedding model: {self.model_name} on {self.device}")
        except Exception as e:
            print(f"Error loading model {self.model_name}: {e}")
            # Fallback to a smaller model
            self.model_name = "all-MiniLM-L6-v2"
            self.model = SentenceTransformer(self.model_name, device=self.device)
            print(f"Fallback to model: {self.model_name}")
    
    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Encode texts into embeddings
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            
        Returns:
            numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        # Preprocess texts
        processed_texts = [self._preprocess_text(text) for text in texts]
        
        # Generate embeddings
        embeddings = self.model.encode(
            processed_texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text into embedding"""
        return self.encode([text])[0]
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before embedding"""
        if not text:
            return ""
        
        # Basic preprocessing
        text = text.strip()
        
        # Truncate if too long
        if len(text) > settings.MAX_SEQUENCE_LENGTH * 4:  # Rough character estimate
            text = text[:settings.MAX_SEQUENCE_LENGTH * 4]
        
        return text
    
    def calculate_similarity(self, embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between embeddings"""
        return cosine_similarity(embeddings1, embeddings2)
    
    def find_similar_texts(
        self, 
        query_text: str, 
        candidate_texts: List[str], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find most similar texts to a query
        
        Args:
            query_text: Query text
            candidate_texts: List of candidate texts
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries with text, similarity score, and index
        """
        if not candidate_texts:
            return []
        
        # Encode query and candidates
        query_embedding = self.encode([query_text])
        candidate_embeddings = self.encode(candidate_texts)
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'text': candidate_texts[idx],
                'similarity': float(similarities[idx]),
                'index': int(idx)
            })
        
        return results
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.model.get_sentence_embedding_dimension()
    
    def batch_encode_with_metadata(
        self, 
        texts: List[str], 
        metadata: List[Dict[str, Any]], 
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        Encode texts with associated metadata
        
        Args:
            texts: List of texts to encode
            metadata: List of metadata dictionaries
            batch_size: Batch size for encoding
            
        Returns:
            List of dictionaries with embeddings and metadata
        """
        if len(texts) != len(metadata):
            raise ValueError("Texts and metadata must have the same length")
        
        embeddings = self.encode(texts, batch_size=batch_size)
        
        results = []
        for i, (text, meta, embedding) in enumerate(zip(texts, metadata, embeddings)):
            results.append({
                'text': text,
                'embedding': embedding,
                'metadata': meta,
                'index': i
            })
        
        return results


class BrandContextEmbedder(TextEmbedder):
    """Extended embedder with brand context awareness"""
    
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name)
        self.brand_embeddings = {}
    
    def add_brand_context(self, brand_id: str, brand_keywords: List[str]):
        """Add brand context for enhanced embeddings"""
        if brand_keywords:
            brand_text = " ".join(brand_keywords)
            self.brand_embeddings[brand_id] = self.encode_single(brand_text)
    
    def encode_with_brand_context(
        self, 
        texts: List[str], 
        brand_id: str, 
        context_weight: float = 0.1
    ) -> np.ndarray:
        """
        Encode texts with brand context
        
        Args:
            texts: List of texts to encode
            brand_id: Brand identifier
            context_weight: Weight for brand context (0.0 to 1.0)
            
        Returns:
            numpy array of context-aware embeddings
        """
        # Get base embeddings
        base_embeddings = self.encode(texts)
        
        # Apply brand context if available
        if brand_id in self.brand_embeddings and context_weight > 0:
            brand_embedding = self.brand_embeddings[brand_id]
            
            # Blend embeddings with brand context
            for i in range(len(base_embeddings)):
                base_embeddings[i] = (
                    (1 - context_weight) * base_embeddings[i] + 
                    context_weight * brand_embedding
                )
                
                # Renormalize
                norm = np.linalg.norm(base_embeddings[i])
                if norm > 0:
                    base_embeddings[i] = base_embeddings[i] / norm
        
        return base_embeddings


# Global embedder instance
_embedder = None

def get_embedder() -> TextEmbedder:
    """Get global embedder instance"""
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedder()
    return _embedder


def get_brand_embedder() -> BrandContextEmbedder:
    """Get global brand-aware embedder instance"""
    global _embedder
    if not isinstance(_embedder, BrandContextEmbedder):
        _embedder = BrandContextEmbedder()
    return _embedder
