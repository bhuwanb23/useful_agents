# phase2-matching/scorers/base_scorer.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from models.scored_jobs import ScoreBreakdown

class BaseScorer(ABC):
    """
    Abstract base class for all scorers
    """
    
    def __init__(self, resume_analysis: Dict[str, Any], preferences: Dict[str, Any]):
        self.resume_analysis = resume_analysis
        self.preferences = preferences
    
    @abstractmethod
    def score(self, job: Dict[str, Any]) -> ScoreBreakdown:
        """
        Score a job and return breakdown
        Must be implemented by subclasses
        """
        pass
    
    def normalize_score(self, score: float, max_score: float) -> float:
        """
        Ensure score doesn't exceed maximum
        """
        return min(score, max_score)
    
    def calculate_total(self, breakdown: ScoreBreakdown) -> float:
        """
        Calculate total score from breakdown
        """
        return sum([
            breakdown.skills_match,
            breakdown.experience_match,
            breakdown.title_match,
            breakdown.semantic_similarity,
            breakdown.salary_match,
            breakdown.location_match,
            breakdown.culture_fit,
            breakdown.growth_potential
        ])