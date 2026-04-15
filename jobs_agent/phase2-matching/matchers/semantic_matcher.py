# phase2-matching/matchers/semantic_matcher.py
from utils.embedding_cache import EmbeddingCache

class SemanticMatcher:
    """
    Semantic similarity using embeddings
    Fast and free using local Sentence-BERT
    """
    
    def __init__(self, cache: EmbeddingCache):
        self.cache = cache
    
    def calculate_match(
        self,
        resume_text: str,
        job_description: str,
        max_score: float = 15.0
    ) -> float:
        """
        Calculate semantic similarity score (max 15 points)
        """
        if not resume_text or not job_description:
            return max_score * 0.5
        
        # Get embeddings
        resume_embedding = self.cache.get_embedding(resume_text)
        job_embedding = self.cache.get_embedding(job_description)
        
        # Calculate cosine similarity
        similarity = self.cache.cosine_similarity(resume_embedding, job_embedding)
        
        # Convert to score (0-1 → 0-max_score)
        score = similarity * max_score
        
        return round(score, 2)