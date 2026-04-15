# models/resume.py
from pydantic import BaseModel
from typing import List, Optional, Dict

class ResumeAnalysis(BaseModel):
    job_titles: List[str]
    skills: List[str]
    experience_years: float = 0.0
    seniority: str = "mid"  # "entry", "mid", "senior"
    industries: List[str] = []
    education: str = ""
    certifications: List[str] = []
    search_queries: List[str] = []
    alternative_titles: List[str] = []
    priority_skills: List[str] = []
    # Optional fields for rule-based parsing
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    years_experience: Optional[int] = None
    links: Optional[Dict[str, str]] = None