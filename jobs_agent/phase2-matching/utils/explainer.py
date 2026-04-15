# phase2-matching/utils/explainer.py
from typing import Dict, List
from models.scored_job import ScoreBreakdown, MatchExplanation
from config.scoring_config import GRADE_THRESHOLDS, RECOMMENDATIONS

class MatchExplainer:
    """
    Generate human-readable explanations of match scores
    """
    
    def __init__(self):
        pass
    
    def create_explanation(
        self,
        breakdown: ScoreBreakdown,
        total_score: float,
        ai_summary: str = "",
        missing_skills: List[str] = None
    ) -> MatchExplanation:
        """
        Create complete match explanation
        """
        explanation = MatchExplanation()
        
        # Identify strengths
        explanation.strengths = self._find_strengths(breakdown)
        
        # Identify concerns
        explanation.concerns = self._find_concerns(breakdown)
        
        # Add missing skills
        if missing_skills:
            explanation.missing_skills = missing_skills
        
        # Add AI summary
        if ai_summary:
            explanation.ai_summary = ai_summary
        
        # Generate recommendation
        explanation.recommendation = self._get_recommendation(total_score)
        
        return explanation
    
    def _find_strengths(self, breakdown: ScoreBreakdown) -> List[str]:
        """
        Identify what makes this a good match
        """
        strengths = []
        scores = breakdown.to_dict()
        
        if scores['skills'] >= 25:
            strengths.append(f"Excellent skills match ({scores['skills']:.1f}/30 points)")
        elif scores['skills'] >= 20:
            strengths.append(f"Strong skills match ({scores['skills']:.1f}/30 points)")
        
        if scores['experience'] >= 12:
            strengths.append(f"Experience level aligns well ({scores['experience']:.1f}/15 points)")
        
        if scores['title'] >= 12:
            strengths.append(f"Job title closely matches background ({scores['title']:.1f}/15 points)")
        
        if scores['semantic'] >= 12:
            strengths.append(f"High overall compatibility ({scores['semantic']:.1f}/15 points)")
        
        if scores['salary'] >= 8:
            strengths.append("Salary meets or exceeds expectations")
        
        if scores['location'] >= 4:
            strengths.append("Location preference matches")
        
        if scores['culture'] >= 4:
            strengths.append("Strong cultural fit indicators")
        
        if scores['growth'] >= 4:
            strengths.append("Excellent growth potential")
        
        return strengths
    
    def _find_concerns(self, breakdown: ScoreBreakdown) -> List[str]:
        """
        Identify potential issues
        """
        concerns = []
        scores = breakdown.to_dict()
        
        if scores['skills'] < 15:
            concerns.append(f"Limited skills overlap ({scores['skills']:.1f}/30 points)")
        
        if scores['experience'] < 8:
            concerns.append(f"Experience level may not align ({scores['experience']:.1f}/15 points)")
        
        if scores['title'] < 8:
            concerns.append("Job title differs from background")
        
        if scores['salary'] < 5:
            concerns.append("Salary may be below expectations")
        
        if scores['location'] < 2:
            concerns.append("Location doesn't match preferences")
        
        if scores['culture'] < 2:
            concerns.append("Cultural fit uncertain")
        
        return concerns
    
    def _get_recommendation(self, total_score: float) -> str:
        """
        Get recommendation based on score
        """
        for grade, threshold in sorted(GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                return RECOMMENDATIONS[grade]
        
        return RECOMMENDATIONS['F']
    
    def score_to_grade(self, total_score: float) -> str:
        """
        Convert numeric score to letter grade
        """
        for grade, threshold in sorted(GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                return grade
        
        return 'F'