# models/preferences.py
from pydantic import BaseModel
from typing import Optional, List

class JobPreferences(BaseModel):
    # Location
    remote_only: bool = False
    locations: List[str] = []  # ["New York", "San Francisco"]
    countries: List[str] = ["USA"]
    
    # Job Details
    job_types: List[str] = ["full-time"]
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    
    # Company
    company_size: Optional[List[str]] = None  # ["startup", "medium", "enterprise"]
    industries: Optional[List[str]] = None
    
    # Search
    results_per_source: int = 50
    max_job_age_days: int = 30
    
    # Exclusions
    excluded_companies: List[str] = []
    excluded_keywords: List[str] = []  # ["unpaid", "volunteer"]