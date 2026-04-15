# models/resume.py
from pydantic import BaseModel
from typing import List, Optional

class ResumeAnalysis(BaseModel):
    job_titles: List[str]
    skills: List[str]
    experience_years: float
    seniority: str  # "entry", "mid", "senior"
    industries: List[str]
    education: str
    certifications: List[str]
    search_queries: List[str]
    alternative_titles: List[str]
    priority_skills: List[str]