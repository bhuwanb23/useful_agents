# models/job.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum

class JobType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"

class Job(BaseModel):
    # Identifiers
    job_id: str  # Unique ID (hash of URL + title)
    source: str  # "jobspy", "apify", "career_page"
    
    # Basic Info
    title: str
    company: str
    location: Optional[str] = None
    is_remote: bool = False
    
    # Details
    description: str
    job_type: Optional[JobType] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    
    # Links
    job_url: HttpUrl
    company_url: Optional[HttpUrl] = None
    application_url: Optional[HttpUrl] = None
    
    # Metadata
    posted_date: Optional[datetime] = None
    scraped_at: datetime = datetime.now()
    
    # Extracted Data
    required_skills: List[str] = []
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    
    # Matching (will be calculated later)
    match_score: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc123",
                "source": "jobspy",
                "title": "Senior Python Developer",
                "company": "TechCorp",
                "location": "Remote",
                "is_remote": True,
                "description": "We are looking for...",
                "job_url": "https://example.com/job/123"
            }
        }