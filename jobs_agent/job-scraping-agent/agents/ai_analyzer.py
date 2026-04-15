# agents/ai_analyzer.py
import google.generativeai as genai
from typing import Dict, Any, List
import json
from config.settings import settings
from config.prompts import RESUME_ANALYSIS_PROMPT, QUERY_ENHANCEMENT_PROMPT
from models.resume import ResumeAnalysis
from models.preferences import JobPreferences

class AIAnalyzer:
    def __init__(self):
        # Using FREE Gemini API
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        # Using gemini-1.5-flash (free tier available)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_resume(self, resume_path: str) -> ResumeAnalysis:
        """
        Analyze resume markdown file and extract structured data
        """
        # Read resume
        with open(resume_path, 'r', encoding='utf-8') as f:
            resume_content = f.read()
        
        # Create prompt
        prompt = RESUME_ANALYSIS_PROMPT.format(resume_content=resume_content)
        
        # Call Gemini
        response = self.model.generate_content(prompt)
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response.text
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis_data = json.loads(response_text.strip())
            return ResumeAnalysis(**analysis_data)
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            print(f"Raw response: {response.text}")
            raise
    
    def generate_search_queries(
        self, 
        resume_analysis: ResumeAnalysis, 
        preferences: JobPreferences
    ) -> List[str]:
        """
        Generate enhanced search queries based on resume and preferences
        """
        prompt = QUERY_ENHANCEMENT_PROMPT.format(
            remote="Yes" if preferences.remote_only else "No",
            location=", ".join(preferences.locations) if preferences.locations else "Any",
            salary_min=preferences.min_salary or "Not specified",
            job_type=", ".join(preferences.job_types),
            analysis=resume_analysis.model_dump_json(indent=2)
        )
        
        response = self.model.generate_content(prompt)
        
        # Parse response
        try:
            response_text = response.text
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            queries = json.loads(response_text.strip())
            
            # Combine with original queries
            all_queries = list(set(resume_analysis.search_queries + queries))
            return all_queries
        except Exception as e:
            print(f"Error generating queries: {e}")
            return resume_analysis.search_queries

# Example usage:
"""
analyzer = AIAnalyzer()
analysis = analyzer.analyze_resume("data/resume.md")
print(f"Found {len(analysis.job_titles)} job titles")
print(f"Generated {len(analysis.search_queries)} search queries")
"""