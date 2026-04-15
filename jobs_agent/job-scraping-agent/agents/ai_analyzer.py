# agents/ai_analyzer.py
import google.generativeai as genai
from typing import Dict, Any, List
import json
from config.settings import settings
from config.prompts import RESUME_ANALYSIS_PROMPT, QUERY_ENHANCEMENT_PROMPT
from models.resume import ResumeAnalysis
from models.preferences import JobPreferences
from utils.resume_parser import ResumeParser

class AIAnalyzer:
    def __init__(self, use_ai=True):
        """
        Initialize AI Analyzer
        
        Args:
            use_ai: If True, use Gemini API. If False, use rule-based parsing (no API key needed)
        """
        self.use_ai = use_ai
        self.resume_parser = ResumeParser()
        
        if use_ai:
            # Using FREE Gemini API
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            # Using gemini-2.0-flash (free tier, currently available)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            print("⚠️  Running in rule-based mode (no AI API). For better results, enable Google AI API.")
            self.model = None
    
    def analyze_resume(self, resume_path: str) -> ResumeAnalysis:
        """
        Analyze resume markdown file and extract structured data
        """
        if not self.use_ai:
            # Use rule-based parsing
            return self._analyze_resume_rule_based(resume_path)
        
        # Use AI-based parsing
        try:
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
        except Exception as e:
            # If AI fails, fallback to rule-based parsing
            print(f"⚠️  AI analysis failed ({str(e)[:100]}...)")
            print("🔄 Falling back to rule-based resume parsing...")
            return self._analyze_resume_rule_based(resume_path)
    
    def generate_search_queries(
        self, 
        resume_analysis: ResumeAnalysis, 
        preferences: JobPreferences
    ) -> List[str]:
        """
        Generate enhanced search queries based on resume and preferences
        """
        if not self.use_ai or self.model is None:
            # Use rule-based query generation
            return self._generate_queries_rule_based(resume_analysis, preferences)
        
        try:
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
        except Exception as e:
            print(f"⚠️  AI query generation failed, using rule-based approach...")
            return self._generate_queries_rule_based(resume_analysis, preferences)
    
    def _analyze_resume_rule_based(self, resume_path: str) -> ResumeAnalysis:
        """
        Rule-based resume analysis (fallback when AI is not available)
        """
        parsed = self.resume_parser.parse_markdown(resume_path)
        
        # Extract job titles from experience
        job_titles = []
        for exp in parsed.get('experience', []):
            title = exp.get('title', '')
            if title:
                job_titles.append(title)
        
        # If no titles found, use generic ones based on skills
        if not job_titles:
            skills = parsed.get('skills', [])
            if 'Python' in skills:
                job_titles.append('Python Developer')
            if 'JavaScript' in skills or 'React' in skills:
                job_titles.append('Frontend Developer')
            if not job_titles:
                job_titles.append('Software Developer')
        
        # Generate search queries from job titles and skills
        skills = parsed.get('skills', [])
        search_queries = []
        for title in job_titles[:3]:  # Top 3 titles
            search_queries.append(title)
            if skills:
                search_queries.append(f"{title} {' '.join(skills[:3])}")
        
        # Determine seniority and experience years from experience count
        exp_count = len(parsed.get('experience', []))
        experience_years = float(exp_count * 2)  # Estimate 2 years per position
        if exp_count >= 5:
            seniority = 'senior'
        elif exp_count >= 3:
            seniority = 'mid'
        else:
            seniority = 'entry'
        
        # Extract education as string
        education_list = parsed.get('education', [])
        education_str = "; ".join([edu.get('degree', '') for edu in education_list]) if education_list else ""
        
        return ResumeAnalysis(
            job_titles=job_titles,
            skills=skills,
            experience_years=experience_years,
            seniority=seniority,
            industries=[],  # Could be extracted from experience
            education=education_str,
            certifications=parsed.get('certifications', []),
            search_queries=search_queries,
            alternative_titles=job_titles[1:] if len(job_titles) > 1 else [],
            priority_skills=skills[:5],  # Top 5 skills
            name=parsed.get('name'),
            email=parsed.get('email'),
            phone=parsed.get('phone'),
            years_experience=exp_count,
            links=parsed.get('links')
        )
    
    def _generate_queries_rule_based(
        self, 
        resume_analysis: ResumeAnalysis, 
        preferences: JobPreferences
    ) -> List[str]:
        """
        Rule-based search query generation (fallback when AI is not available)
        """
        queries = list(resume_analysis.search_queries)
        
        # Add location-based queries
        if preferences.locations:
            for location in preferences.locations[:2]:
                for title in resume_analysis.job_titles[:2]:
                    queries.append(f"{title} {location}")
        
        # Add remote queries
        if preferences.remote_only:
            for title in resume_analysis.job_titles[:3]:
                queries.append(f"{title} remote")
                queries.append(f"remote {title}")
        
        # Add skill-based queries
        if resume_analysis.skills:
            top_skills = resume_analysis.skills[:5]
            for skill in top_skills:
                queries.append(f"{skill} developer")
        
        # Remove duplicates and return
        return list(set(queries))

# Example usage:
"""
analyzer = AIAnalyzer()
analysis = analyzer.analyze_resume("data/resume.md")
print(f"Found {len(analysis.job_titles)} job titles")
print(f"Generated {len(analysis.search_queries)} search queries")
"""