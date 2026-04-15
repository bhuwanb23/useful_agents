# phase2-matching/utils/embedding_cache.py
import pickle
import hashlib
from pathlib import Path
from typing import Optional, List
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingCache:
    """
    Cache embeddings to avoid recomputation
    Uses local Sentence-BERT model (free, fast)
    """
    
    def __init__(self, cache_file: str = "data/embeddings_cache.pkl", 
                 model_name: str = "all-MiniLM-L6-v2"):
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        
        # Load sentence transformer model (downloads on first use)
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("✓ Model loaded")
    
    def _load_cache(self) -> dict:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
    
    def _get_hash(self, text: str) -> str:
        """Create hash key for text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text (cached)
        """
        text_hash = self._get_hash(text)
        
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        # Compute embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Cache it
        self.cache[text_hash] = embedding
        
        return embedding
    
    def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Get embeddings for multiple texts (batch processing)
        """
        embeddings = []
        texts_to_compute = []
        indices_to_compute = []
        
        # Check cache first
        for i, text in enumerate(texts):
            text_hash = self._get_hash(text)
            if text_hash in self.cache:
                embeddings.append(self.cache[text_hash])
            else:
                embeddings.append(None)  # Placeholder
                texts_to_compute.append(text)
                indices_to_compute.append(i)
        
        # Compute missing embeddings in batch
        if texts_to_compute:
            new_embeddings = self.model.encode(
                texts_to_compute, 
                convert_to_numpy=True,
                show_progress_bar=True
            )
            
            # Fill in placeholders and cache
            for i, embedding in zip(indices_to_compute, new_embeddings):
                embeddings[i] = embedding
                text_hash = self._get_hash(texts[i])
                self.cache[text_hash] = embedding
        
        return embeddings
    
    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def save(self):
        """Save cache to disk"""
        self._save_cache()
        print(f"✓ Saved {len(self.cache)} embeddings to cache")
    
    def clear(self):
        """Clear cache"""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()