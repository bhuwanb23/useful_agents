# phase2-matching/matchers/title_matcher.py
from typing import List
from difflib import SequenceMatcher

class TitleMatcher:
    """
    Match job titles using keyword overlap and fuzzy matching
    """
    
    # Common title synonyms
    TITLE_SYNONYMS = {
        'software engineer': ['software developer', 'developer', 'programmer', 'engineer'],
        'backend engineer': ['backend developer', 'server-side engineer', 'api developer'],
        'frontend engineer': ['frontend developer', 'ui engineer', 'web developer'],
        'full stack': ['fullstack', 'full-stack', 'full stack developer'],
        'data scientist': ['ml engineer', 'data analyst', 'research scientist'],
        'devops': ['sre', 'platform engineer', 'infrastructure engineer'],
    }
    
    def __init__(self):
        pass
    
    def calculate_match(
        self,
        resume_titles: List[str],
        job_title: str,
        max_score: float = 15.0
    ) -> float:
        """
        Calculate title match score (max 15 points)
        """
        if not resume_titles or not job_title:
            return max_score * 0.3  # Neutral score
        
        job_title_lower = job_title.lower().strip()
        
        best_match_score = 0.0
        
        for resume_title in resume_titles:
            resume_title_lower = resume_title.lower().strip()
            
            # Exact match
            if resume_title_lower == job_title_lower:
                return max_score  # Perfect match!
            
            # Keyword overlap
            keyword_score = self._keyword_overlap(resume_title_lower, job_title_lower)
            
            # Fuzzy string similarity
            fuzzy_score = SequenceMatcher(None, resume_title_lower, job_title_lower).ratio()
            
            # Synonym match
            synonym_score = self._check_synonyms(resume_title_lower, job_title_lower)
            
            # Combined score (weighted)
            combined = (keyword_score * 0.5 + fuzzy_score * 0.3 + synonym_score * 0.2)
            
            best_match_score = max(best_match_score, combined)
        
        return round(best_match_score * max_score, 2)
    
    def _keyword_overlap(self, title1: str, title2: str) -> float:
        """
        Calculate keyword overlap between titles
        """
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for'}
        
        words1 = set(title1.split()) - stop_words
        words2 = set(title2.split()) - stop_words
        
        if not words2:
            return 0.0
        
        overlap = len(words1 & words2)
        return overlap / len(words2)
    
    def _check_synonyms(self, title1: str, title2: str) -> float:
        """
        Check if titles are synonyms
        """
        for base_title, synonyms in self.TITLE_SYNONYMS.items():
            base_in_1 = base_title in title1
            base_in_2 = base_title in title2
            synonym_in_1 = any(syn in title1 for syn in synonyms)
            synonym_in_2 = any(syn in title2 for syn in synonyms)
            
            if (base_in_1 or synonym_in_1) and (base_in_2 or synonym_in_2):
                return 1.0
        
        return 0.0