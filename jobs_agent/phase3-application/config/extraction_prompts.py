"""
AI prompts for resume extraction
"""

RESUME_EXTRACTION_PROMPT = """
You are an expert resume parser. Extract ALL information from this resume with high accuracy.

Resume Content:
{resume_text}

Extract the following information. For each field, provide:
1. The extracted value
2. Confidence score (0.0 to 1.0)
3. Source (where in resume you found it)
4. Reasoning (why you chose this value)

Return ONLY valid JSON in this EXACT format:

{{
  "personal_info": {{
    "first_name": {{"value": "John", "confidence": 0.95, "source": "resume_header", "reasoning": "Found in header"}},
    "last_name": {{"value": "Doe", "confidence": 0.95, "source": "resume_header", "reasoning": "Found in header"}},
    "email": {{"value": "john@email.com", "confidence": 1.0, "source": "resume_contact"}},
    "phone": {{"value": "+1-555-0123", "confidence": 0.90, "source": "resume_contact"}},
    "city": {{"value": "San Francisco", "confidence": 0.80, "source": "ai_inference", "reasoning": "Inferred from location"}},
    "state": {{"value": "CA", "confidence": 0.80, "source": "ai_inference"}},
    "country": {{"value": "USA", "confidence": 0.85, "source": "ai_inference"}},
    "linkedin_url": {{"value": "https://linkedin.com/in/johndoe", "confidence": 1.0, "source": "resume_links"}},
    "github_url": {{"value": "https://github.com/johndoe", "confidence": 1.0, "source": "resume_links"}},
    "portfolio_url": {{"value": "https://johndoe.dev", "confidence": 1.0, "source": "resume_links"}}
  }},
  "professional_info": {{
    "current_title": {{"value": "Senior Software Engineer", "confidence": 0.95, "source": "resume_experience"}},
    "current_company": {{"value": "TechCorp", "confidence": 0.95, "source": "resume_experience"}},
    "years_of_experience": {{"value": 5, "confidence": 0.90, "source": "calculated", "reasoning": "2019-2024"}},
    "seniority_level": {{"value": "senior", "confidence": 0.90, "source": "ai_inference"}},
    "job_titles": {{"value": ["Senior Software Engineer", "Software Engineer"], "confidence": 0.95}},
    "industries": {{"value": ["SaaS", "Technology"], "confidence": 0.80, "source": "ai_inference"}}
  }},
  "skills": {{
    "all_skills": {{"value": ["Python", "JavaScript", "FastAPI", "React"], "confidence": 0.95}},
    "programming_languages": {{"value": ["Python", "JavaScript"], "confidence": 0.98}},
    "frameworks": {{"value": ["FastAPI", "React"], "confidence": 0.95}},
    "skills_with_years": {{
      "Python": {{"years": 5, "confidence": 0.90, "reasoning": "Mentioned in all jobs"}},
      "JavaScript": {{"years": 3, "confidence": 0.85}}
    }}
  }},
  "education": {{
    "highest_degree": {{"value": "Bachelor of Science in Computer Science", "confidence": 0.95}},
    "institution": {{"value": "University of Tech", "confidence": 0.95}},
    "graduation_year": {{"value": 2018, "confidence": 0.95}}
  }}
}}

IMPORTANT:
- Use null for fields not found
- Confidence must be 0.0-1.0
- Be conservative with confidence scores
- For inferred data, confidence should be <= 0.80
"""


SKILL_YEARS_EXTRACTION_PROMPT = """
Analyze this resume and determine years of experience for each skill.

Resume:
{resume_text}

Skills to analyze:
{skills_list}

For each skill, determine:
1. Years of experience (float)
2. Confidence (0.0-1.0)
3. Evidence (where you found it)

Return JSON:
{{
  "Python": {{"years": 5.0, "confidence": 0.90, "evidence": "Mentioned in all 3 jobs from 2019-2024"}},
  "React": {{"years": 2.0, "confidence": 0.80, "evidence": "Mentioned in last 2 jobs"}}
}}
"""


WORK_AUTHORIZATION_DETECTION_PROMPT = """
Check if this resume mentions work authorization or visa status.

Resume:
{resume_text}

Look for phrases like:
- "US Citizen"
- "Green Card"
- "H1B"
- "Authorized to work"
- "Require sponsorship"

Return JSON:
{{
  "work_authorization": {{"value": "US Citizen", "confidence": 0.95, "source": "resume_header"}},
  "requires_sponsorship": {{"value": false, "confidence": 0.90}}
}}

If not found, return null values with 0.0 confidence.
"""