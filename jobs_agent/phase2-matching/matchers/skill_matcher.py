# phase2-matching/matchers/skill_matcher.py
from typing import List, Set
from difflib import SequenceMatcher
from utils.skill_extractor import SkillExtractor

class SkillMatcher:
    """
    Match skills between resume and job
    Traditional keyword matching + fuzzy matching
    """
    
    def __init__(self, fuzzy_threshold: float = 0.85):
        self.extractor = SkillExtractor()
        self.fuzzy_threshold = fuzzy_threshold
    
    def calculate_match(
        self, 
        resume_skills: List[str], 
        job_description: str,
        max_score: float = 30.0
    ) -> float:
        """
        Calculate skill match score (max 30 points)
        20 points: exact/fuzzy matches
        10 points: skill density (how many skills mentioned)
        """
        # Extract job skills
        job_skills = self.extractor.extract_skills(job_description)
        
        if not job_skills:
            return max_score * 0.5  # Neutral score if can't extract skills
        
        # Normalize
        resume_skills_lower = {s.lower().strip() for s in resume_skills}
        job_skills_lower = {s.lower().strip() for s in job_skills}
        
        # Exact matches
        exact_matches = resume_skills_lower & job_skills_lower
        exact_match_score = len(exact_matches) / len(job_skills_lower)
        
        # Fuzzy matches for remaining
        remaining_job_skills = job_skills_lower - exact_matches
        remaining_resume_skills = resume_skills_lower - exact_matches
        
        fuzzy_matches = 0
        for job_skill in remaining_job_skills:
            for resume_skill in remaining_resume_skills:
                similarity = SequenceMatcher(None, job_skill, resume_skill).ratio()
                if similarity >= self.fuzzy_threshold:
                    fuzzy_matches += 1
                    break
        
        fuzzy_match_score = fuzzy_matches / len(job_skills_lower) if job_skills_lower else 0
        
        # Combined match rate
        total_match_rate = exact_match_score + (fuzzy_match_score * 0.8)  # Fuzzy worth less
        total_match_rate = min(1.0, total_match_rate)  # Cap at 100%
        
        # Skill density bonus (candidate has many relevant skills)
        density_score = min(1.0, len(resume_skills_lower) / 20)  # 20+ skills = max density
        
        # Calculate final score
        match_score = (total_match_rate * 0.70 + density_score * 0.30) * max_score
        
        return round(match_score, 2)
    
    def get_matched_skills(
        self, 
        resume_skills: List[str], 
        job_description: str
    ) -> dict:
        """
        Return detailed skill matching info
        """
        job_skills = self.extractor.extract_skills(job_description)
        
        resume_skills_lower = {s.lower().strip() for s in resume_skills}
        job_skills_lower = {s.lower().strip() for s in job_skills}
        
        matched = list(resume_skills_lower & job_skills_lower)
        missing = list(job_skills_lower - resume_skills_lower)
        
        return {
            'matched_skills': matched,
            'missing_skills': missing,
            'match_rate': len(matched) / len(job_skills_lower) if job_skills_lower else 0,
            'total_job_skills': len(job_skills_lower),
            'total_resume_skills': len(resume_skills_lower)
        }