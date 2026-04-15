# phase2-matching/scorers/hybrid_scorer.py
from typing import Dict, Any
from .base_scorer import BaseScorer
from .traditional_scorer import TraditionalScorer
from .ai_scorer import AIScorer
from models.scored_jobs import ScoreBreakdown

class HybridScorer(BaseScorer):
    """
    Combines traditional and AI scoring
    Best of both worlds!
    """
    
    def __init__(
        self, 
        resume_analysis: Dict[str, Any], 
        preferences: Dict[str, Any],
        api_key: str,
        embedding_cache=None,
        use_ai: bool = True
    ):
        super().__init__(resume_analysis, preferences)
        
        # Initialize traditional scorer
        self.traditional_scorer = TraditionalScorer(resume_analysis, preferences)
        
        # Initialize AI scorer (optional)
        self.use_ai = use_ai
        if use_ai:
            self.ai_scorer = AIScorer(resume_analysis, preferences, api_key, embedding_cache)
        else:
            self.ai_scorer = None
    
    def score(self, job: Dict[str, Any], resume_text: str = "") -> ScoreBreakdown:
        """
        Complete scoring using both traditional and AI methods
        """
        # Get traditional scores (fast, deterministic)
        breakdown = self.traditional_scorer.score(job)
        
        if self.use_ai and self.ai_scorer:
            # Add semantic similarity (15 points)
            if resume_text:
                breakdown.semantic_similarity = self.ai_scorer.score_semantic_similarity(
                    resume_text=resume_text,
                    job_description=job.get('description', '')
                )
            
            # Add culture fit (5 points)
            breakdown.culture_fit = self.ai_scorer.score_culture_fit(job)
            
            # Add growth potential (5 points)
            breakdown.growth_potential = self.ai_scorer.score_growth_potential(job)
        else:
            # Use neutral scores if AI disabled
            breakdown.semantic_similarity = 7.5
            breakdown.culture_fit = 2.5
            breakdown.growth_potential = 2.5
        
        return breakdown
    
    def score_with_explanation(
        self, 
        job: Dict[str, Any], 
        resume_text: str = ""
    ) -> tuple[ScoreBreakdown, str, list]:
        """
        Score job and generate explanation
        Returns: (breakdown, explanation, missing_skills)
        """
        # Get scores
        breakdown = self.score(job, resume_text)
        
        # Calculate total
        total_score = self.calculate_total(breakdown)
        
        # Generate explanation and find missing skills (if AI enabled)
        explanation = ""
        missing_skills = []
        
        if self.use_ai and self.ai_scorer:
            try:
                explanation = self.ai_scorer.generate_explanation(job, total_score)
                missing_skills = self.ai_scorer.find_missing_skills(job)
            except Exception as e:
                print(f"Error generating AI explanation: {e}")
        
        return breakdown, explanation, missing_skills