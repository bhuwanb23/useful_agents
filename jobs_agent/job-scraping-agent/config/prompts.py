# config/prompts.py
RESUME_ANALYSIS_PROMPT = """
You are an expert career advisor and job search specialist.

Analyze the following resume and extract:
1. **Primary job titles** the candidate is qualified for
2. **Key technical skills** and tools
3. **Years of experience** in different areas
4. **Industry/domain expertise**
5. **Education level and fields**
6. **Relevant certifications**

Then generate:
- 10 optimized job search queries (mixing titles, skills, and levels)
- Alternative job titles to search for
- Key skills to prioritize in job matching
- Seniority level (entry/mid/senior)

Resume:
{resume_content}

Return ONLY valid JSON in this format:
{{
    "job_titles": ["Software Engineer", "Backend Developer"],
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience_years": 3,
    "seniority": "mid",
    "industries": ["SaaS", "FinTech"],
    "education": "Bachelor's in Computer Science",
    "certifications": ["AWS Certified"],
    "search_queries": [
        "Python Backend Developer",
        "Mid-level Software Engineer Python",
        ...
    ],
    "alternative_titles": ["Python Developer", "Full Stack Engineer"],
    "priority_skills": ["Python", "APIs", "Databases"]
}}
"""

QUERY_ENHANCEMENT_PROMPT = """
Given these user preferences and resume analysis, generate comprehensive search queries:

Preferences:
- Remote: {remote}
- Location: {location}
- Salary Min: {salary_min}
- Job Type: {job_type}

Resume Analysis:
{analysis}

Generate 15 diverse search queries that combine:
- Job titles with experience level
- Key skills combinations
- Location/remote preferences
- Industry-specific terms

Return as JSON array of strings.
"""