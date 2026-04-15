# phase2-matching/scorers/traditional_scorer.py
from typing import Dict, Any
from .base_scorer import BaseScorer
from models.scored_job import ScoreBreakdown
from matchers import (
    SkillMatcher,
    ExperienceMatcher,
    TitleMatcher,
    SalaryMatcher,
    LocationMatcher
)

class TraditionalScorer(BaseScorer):
    """
    Traditional rule-based scoring (no AI)
    Fast and deterministic
    """
    
    def __init__(self, resume_analysis: Dict[str, Any], preferences: Dict[str, Any]):
        super().__init__(resume_analysis, preferences)
        
        # Initialize matchers
        self.skill_matcher = SkillMatcher()
        self.experience_matcher = ExperienceMatcher()
        self.title_matcher = TitleMatcher()
        self.salary_matcher = SalaryMatcher()
        self.location_matcher = LocationMatcher()
    
    def score(self, job: Dict[str, Any]) -> ScoreBreakdown:
        """
        Score job using traditional methods
        """
        breakdown = ScoreBreakdown()
        
        # 1. Skills match (30 points)
        breakdown.skills_match = self.skill_matcher.calculate_match(
            resume_skills=self.resume_analysis.get('skills', []),
            job_description=job.get('description', ''),
            max_score=30.0
        )
        
        # 2. Experience match (15 points)
        breakdown.experience_match = self.experience_matcher.calculate_match(
            resume_years=self.resume_analysis.get('experience_years', 0),
            resume_seniority=self.resume_analysis.get('seniority', 'mid'),
            job_title=job.get('title', ''),
            job_description=job.get('description', ''),
            max_score=15.0
        )
        
        # 3. Title match (15 points)
        breakdown.title_match = self.title_matcher.calculate_match(
            resume_titles=self.resume_analysis.get('job_titles', []),
            job_title=job.get('title', ''),
            max_score=15.0
        )
        
        # 4. Salary match (10 points)
        breakdown.salary_match = self.salary_matcher.calculate_match(
            min_expected=self.preferences.get('min_salary'),
            job_min=job.get('salary_min'),
            job_max=job.get('salary_max'),
            max_score=10.0
        )
        
        # 5. Location match (5 points)
        breakdown.location_match = self.location_matcher.calculate_match(
            preferred_locations=self.preferences.get('locations', []),
            remote_only=self.preferences.get('remote_only', False),
            job_location=job.get('location'),
            job_is_remote=job.get('is_remote', False),
            max_score=5.0
        )
        
        # Note: semantic, culture, and growth are 0 (filled by AI scorer)
        
        return breakdown