# phase2-matching/models/scored_job.py
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class MatchGrade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"

class ScoreBreakdown(BaseModel):
    """Detailed score breakdown"""
    skills_match: float = 0.0
    experience_match: float = 0.0
    title_match: float = 0.0
    semantic_similarity: float = 0.0
    salary_match: float = 0.0
    location_match: float = 0.0
    culture_fit: float = 0.0
    growth_potential: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'skills': self.skills_match,
            'experience': self.experience_match,
            'title': self.title_match,
            'semantic': self.semantic_similarity,
            'salary': self.salary_match,
            'location': self.location_match,
            'culture': self.culture_fit,
            'growth': self.growth_potential
        }

class MatchExplanation(BaseModel):
    """Human-readable explanation of the match"""
    strengths: List[str] = []
    concerns: List[str] = []
    missing_skills: List[str] = []
    ai_summary: Optional[str] = None
    recommendation: str = ""

class ScoredJob(BaseModel):
    """Job with matching score and analysis"""
    
    # Original job data
    job_id: str
    title: str
    company: str
    location: Optional[str]
    is_remote: bool
    job_url: str
    description: str
    salary_min: Optional[float]
    salary_max: Optional[float]
    posted_date: Optional[datetime]
    source: str
    
    # Matching scores
    total_score: float
    grade: MatchGrade
    breakdown: ScoreBreakdown
    
    # Analysis
    explanation: MatchExplanation
    
    # Metadata
    scored_at: datetime = datetime.now()
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @property
    def score_percentage(self) -> int:
        """Score as percentage"""
        return int(self.total_score)
    
    @property
    def is_recommended(self) -> bool:
        """Should apply to this job?"""
        return self.total_score >= 65  # B grade or higher