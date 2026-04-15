# phase2-matching/scorers/ai_scorer.py
from typing import Dict, Any, List
import google.generativeai as genai
from .base_scorer import BaseScorer
from models.scored_job import ScoreBreakdown
from config.prompts import (
    CULTURE_FIT_PROMPT,
    GROWTH_POTENTIAL_PROMPT,
    MATCH_EXPLANATION_PROMPT,
    MISSING_SKILLS_ANALYSIS_PROMPT
)
import json
import re

class AIScorer(BaseScorer):
    """
    AI-powered scoring using Google Gemini
    Used for semantic analysis and soft factors
    """
    
    def __init__(
        self, 
        resume_analysis: Dict[str, Any], 
        preferences: Dict[str, Any],
        api_key: str,
        embedding_cache=None
    ):
        super().__init__(resume_analysis, preferences)
        
        # Initialize Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Embedding cache for semantic matching
        self.embedding_cache = embedding_cache
        
        # Cache for AI responses
        self.response_cache = {}
    
    def score_semantic_similarity(
        self, 
        resume_text: str, 
        job_description: str
    ) -> float:
        """
        Calculate semantic similarity using embeddings (15 points)
        """
        if not self.embedding_cache:
            return 7.5  # Neutral score if no cache
        
        from matchers.semantic_matcher import SemanticMatcher
        semantic_matcher = SemanticMatcher(self.embedding_cache)
        
        return semantic_matcher.calculate_match(
            resume_text=resume_text,
            job_description=job_description,
            max_score=15.0
        )
    
    def score_culture_fit(self, job: Dict[str, Any]) -> float:
        """
        AI analyzes cultural fit (5 points)
        """
        cache_key = f"culture_{job.get('job_id')}"
        
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]
        
        prompt = CULTURE_FIT_PROMPT.format(
            seniority=self.resume_analysis.get('seniority', 'mid'),
            industries=', '.join(self.resume_analysis.get('industries', [])),
            current_role=self.resume_analysis.get('job_titles', [''])[0],
            job_description=job.get('description', '')[:800],
            company=job.get('company', 'Unknown')
        )
        
        try:
            response = self.model.generate_content(prompt)
            score = self._extract_number(response.text, max_value=5.0)
            self.response_cache[cache_key] = score
            return score
        except Exception as e:
            print(f"AI culture scoring error: {e}")
            return 2.5  # Neutral score on error
    
    def score_growth_potential(self, job: Dict[str, Any]) -> float:
        """
        AI analyzes growth potential (5 points)
        """
        cache_key = f"growth_{job.get('job_id')}"
        
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]
        
        prompt = GROWTH_POTENTIAL_PROMPT.format(
            skills=', '.join(self.resume_analysis.get('priority_skills', [])[:10]),
            seniority=self.resume_analysis.get('seniority', 'mid'),
            job_titles=', '.join(self.resume_analysis.get('job_titles', [])),
            job_description=job.get('description', '')[:800]
        )
        
        try:
            response = self.model.generate_content(prompt)
            score = self._extract_number(response.text, max_value=5.0)
            self.response_cache[cache_key] = score
            return score
        except Exception as e:
            print(f"AI growth scoring error: {e}")
            return 2.5  # Neutral score on error
    
    def generate_explanation(
        self, 
        job: Dict[str, Any], 
        total_score: float
    ) -> str:
        """
        Generate AI explanation of the match
        """
        resume_summary = self._create_resume_summary()
        
        prompt = MATCH_EXPLANATION_PROMPT.format(
            resume_summary=resume_summary,
            title=job.get('title', ''),
            company=job.get('company', ''),
            description=job.get('description', '')[:500],
            score=int(total_score)
        )
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"AI explanation error: {e}")
            return "Match analysis unavailable."
    
    def find_missing_skills(self, job: Dict[str, Any]) -> List[str]:
        """
        AI identifies missing skills
        """
        prompt = MISSING_SKILLS_ANALYSIS_PROMPT.format(
            candidate_skills=', '.join(self.resume_analysis.get('skills', [])),
            job_description=job.get('description', '')[:1000]
        )
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON array
            text = response.text
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            missing = json.loads(text.strip())
            return missing[:5]  # Max 5
        except Exception as e:
            print(f"AI missing skills error: {e}")
            return []
    
    def score_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """
        Score multiple jobs for AI components (culture + growth)
        More efficient than one-by-one
        """
        results = []
        
        for job in jobs:
            culture_score = self.score_culture_fit(job)
            growth_score = self.score_growth_potential(job)
            
            results.append({
                'job_id': job.get('job_id'),
                'culture_fit': culture_score,
                'growth_potential': growth_score
            })
        
        return results
    
    def _extract_number(self, text: str, max_value: float) -> float:
        """
        Extract number from AI response
        """
        # Try to find a number
        numbers = re.findall(r'\d+\.?\d*', text)
        
        if numbers:
            try:
                score = float(numbers[0])
                return min(score, max_value)
            except:
                pass
        
        return max_value / 2  # Neutral score if can't parse
    
    def _create_resume_summary(self) -> str:
        """
        Create brief resume summary for prompts
        """
        summary_parts = []
        
        if self.resume_analysis.get('job_titles'):
            summary_parts.append(f"Role: {self.resume_analysis['job_titles'][0]}")
        
        if self.resume_analysis.get('experience_years'):
            summary_parts.append(f"{self.resume_analysis['experience_years']} years experience")
        
        if self.resume_analysis.get('priority_skills'):
            skills = ', '.join(self.resume_analysis['priority_skills'][:5])
            summary_parts.append(f"Skills: {skills}")
        
        return ' | '.join(summary_parts)