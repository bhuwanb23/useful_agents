# phase2-matching/matchers/experience_matcher.py
import re
from typing import Optional

class ExperienceMatcher:
    """
    Match experience level and years
    """
    
    # Keywords for experience levels
    SENIORITY_KEYWORDS = {
        'entry': ['junior', 'entry', 'graduate', 'associate', 'jr'],
        'mid': ['mid', 'intermediate', 'professional', 'engineer ii', 'engineer 2'],
        'senior': ['senior', 'lead', 'sr', 'principal', 'staff', 'engineer iii', 'engineer 3'],
        'expert': ['expert', 'architect', 'distinguished', 'fellow', 'director', 'vp', 'chief']
    }
    
    SENIORITY_YEARS = {
        'entry': (0, 2),
        'mid': (2, 5),
        'senior': (5, 10),
        'expert': (10, 100)
    }
    
    def __init__(self, tolerance_years: int = 1):
        self.tolerance_years = tolerance_years
    
    def calculate_match(
        self,
        resume_years: float,
        resume_seniority: str,
        job_title: str,
        job_description: str,
        max_score: float = 15.0
    ) -> float:
        """
        Calculate experience match score (max 15 points)
        """
        # Extract required years from description
        required_years = self._extract_required_years(job_description)
        
        # Extract job seniority from title
        job_seniority = self._extract_seniority(job_title)
        
        # Score components
        years_score = self._score_years(resume_years, required_years) * 0.6
        seniority_score = self._score_seniority(resume_seniority, job_seniority) * 0.4
        
        total_score = (years_score + seniority_score) * max_score
        
        return round(total_score, 2)
    
    def _extract_required_years(self, description: str) -> Optional[float]:
        """
        Extract required years from job description
        """
        # Patterns like "3+ years", "5-7 years", "minimum 4 years"
        patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)\s*-\s*\d+\s*years?',
            r'minimum\s*(\d+)\s*years?',
            r'at least\s*(\d+)\s*years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                return float(match.group(1))
        
        return None
    
    def _extract_seniority(self, title: str) -> str:
        """
        Extract seniority level from job title
        """
        title_lower = title.lower()
        
        for level, keywords in self.SENIORITY_KEYWORDS.items():
            if any(keyword in title_lower for keyword in keywords):
                return level
        
        return 'mid'  # Default
    
    def _score_years(self, resume_years: float, required_years: Optional[float]) -> float:
        """
        Score based on years of experience
        Returns 0-1
        """
        if required_years is None:
            return 1.0  # No requirement = full score
        
        if resume_years >= required_years:
            # Meet or exceed requirement
            excess = resume_years - required_years
            
            if excess <= self.tolerance_years:
                return 1.0  # Perfect match
            elif excess <= self.tolerance_years + 2:
                return 0.9  # Slightly overqualified
            else:
                return 0.7  # Overqualified (might be rejected)
        else:
            # Below requirement
            gap = required_years - resume_years
            
            if gap <= self.tolerance_years:
                return 0.8  # Close enough
            elif gap <= 2:
                return 0.5  # Noticeable gap
            else:
                return 0.2  # Too junior
    
    def _score_seniority(self, resume_level: str, job_level: str) -> float:
        """
        Score based on seniority level match
        Returns 0-1
        """
        levels = ['entry', 'mid', 'senior', 'expert']
        
        try:
            resume_idx = levels.index(resume_level)
            job_idx = levels.index(job_level)
        except ValueError:
            return 0.5  # Unknown level
        
        diff = abs(resume_idx - job_idx)
        
        if diff == 0:
            return 1.0  # Exact match
        elif diff == 1:
            return 0.7  # One level off
        elif diff == 2:
            return 0.4  # Two levels off
        else:
            return 0.1  # Too far apart