# agents/search_query_generator.py
from typing import List, Set
from models.resume import ResumeAnalysis
from models.preferences import JobPreferences
import itertools

class SearchQueryGenerator:
    """
    Generates diverse search queries from resume analysis and preferences
    Combines job titles, skills, locations, and modifiers
    """
    
    def __init__(self):
        self.seniority_modifiers = {
            'entry': ['Junior', 'Entry Level', 'Associate', 'Graduate'],
            'mid': ['Mid-level', 'Intermediate', 'Professional'],
            'senior': ['Senior', 'Lead', 'Principal', 'Staff'],
            'expert': ['Expert', 'Architect', 'Distinguished', 'Fellow']
        }
        
        self.job_type_modifiers = {
            'remote': ['Remote', 'Work from Home', 'Distributed'],
            'hybrid': ['Hybrid'],
            'onsite': ['On-site', 'In-office']
        }
    
    def generate_queries(
        self, 
        resume_analysis: ResumeAnalysis,
        preferences: JobPreferences,
        max_queries: int = 50
    ) -> List[str]:
        """
        Generate comprehensive search queries
        """
        queries = set()
        
        # 1. Direct job title queries
        queries.update(self._generate_title_queries(resume_analysis, preferences))
        
        # 2. Skill-based queries
        queries.update(self._generate_skill_queries(resume_analysis, preferences))
        
        # 3. Combined title + skill queries
        queries.update(self._generate_combined_queries(resume_analysis, preferences))
        
        # 4. Industry-specific queries
        queries.update(self._generate_industry_queries(resume_analysis, preferences))
        
        # 5. Alternative title queries
        queries.update(self._generate_alternative_queries(resume_analysis, preferences))
        
        # Convert to list and limit
        query_list = list(queries)[:max_queries]
        
        # Sort by priority (simpler queries first, then complex)
        query_list.sort(key=lambda x: (len(x.split()), x))
        
        return query_list
    
    def _generate_title_queries(
        self,
        resume_analysis: ResumeAnalysis,
        preferences: JobPreferences
    ) -> Set[str]:
        """Generate queries from job titles"""
        queries = set()
        
        seniority_terms = self.seniority_modifiers.get(
            resume_analysis.seniority, 
            []
        )
        
        for title in resume_analysis.job_titles:
            # Direct title
            queries.add(title)
            
            # Title with seniority
            for modifier in seniority_terms:
                queries.add(f"{modifier} {title}")
            
            # Title with remote modifier
            if preferences.remote_only:
                queries.add(f"Remote {title}")
        
        return queries
    
    def _generate_skill_queries(
        self,
        resume_analysis: ResumeAnalysis,
        preferences: JobPreferences
    ) -> Set[str]:
        """Generate queries from top skills"""
        queries = set()
        
        # Take top 5 priority skills
        top_skills = resume_analysis.priority_skills[:5]
        
        # Single skill queries
        for skill in top_skills:
            queries.add(f"{skill} Developer")
            queries.add(f"{skill} Engineer")
        
        # Skill combinations (2 skills max)
        for skill1, skill2 in itertools.combinations(top_skills[:3], 2):
            queries.add(f"{skill1} {skill2} Developer")
        
        return queries
    
    def _generate_combined_queries(
        self,
        resume_analysis: ResumeAnalysis,
        preferences: JobPreferences
    ) -> Set[str]:
        """Combine titles with top skills"""
        queries = set()
        
        # Top 3 titles and top 3 skills
        top_titles = resume_analysis.job_titles[:3]
        top_skills = resume_analysis.priority_skills[:3]
        
        for title in top_titles:
            for skill in top_skills:
                queries.add(f"{title} {skill}")
                queries.add(f"{skill} {title}")
        
        return queries
    
    def _generate_industry_queries(
        self,
        resume_analysis: ResumeAnalysis,
        preferences: JobPreferences
    ) -> Set[str]:
        """Generate industry-specific queries"""
        queries = set()
        
        for title in resume_analysis.job_titles[:3]:
            for industry in resume_analysis.industries[:2]:
                queries.add(f"{title} {industry}")
        
        return queries
    
    def _generate_alternative_queries(
        self,
        resume_analysis: ResumeAnalysis,
        preferences: JobPreferences
    ) -> Set[str]:
        """Use alternative job titles"""
        queries = set()
        
        for alt_title in resume_analysis.alternative_titles[:5]:
            queries.add(alt_title)
            
            if preferences.remote_only:
                queries.add(f"Remote {alt_title}")
        
        return queries

# Example Usage:
"""
generator = SearchQueryGenerator()
queries = generator.generate_queries(resume_analysis, preferences)
print(f"Generated {len(queries)} queries:")
for q in queries[:10]:
    print(f"  - {q}")
"""