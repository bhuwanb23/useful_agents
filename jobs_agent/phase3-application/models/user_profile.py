"""
User Profile - Final verified profile after review
This is what gets used for applications
"""

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class WorkAuthorization(str, Enum):
    """Work authorization status"""
    US_CITIZEN = "US Citizen"
    GREEN_CARD = "Green Card Holder"
    H1B = "H1B Visa"
    OPT = "OPT (F1)"
    REQUIRE_SPONSORSHIP = "Require Sponsorship"
    OTHER = "Other"


class JobType(str, Enum):
    """Preferred job types"""
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class PersonalInfo(BaseModel):
    """Verified personal information"""
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    
    # Location
    city: str
    state: str
    country: str = "USA"
    zip_code: Optional[str] = None
    
    # Social links
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    twitter_url: Optional[HttpUrl] = None
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def location_string(self) -> str:
        """Format: City, State"""
        return f"{self.city}, {self.state}"


class ProfessionalInfo(BaseModel):
    """Verified professional information"""
    current_title: str
    current_company: Optional[str] = None
    years_of_experience: float
    seniority_level: str  # entry, mid, senior, expert
    
    # Job preferences
    job_titles: List[str] = []  # Titles interested in
    industries: List[str] = []
    
    # Availability
    notice_period: str = "2 weeks"
    willing_to_relocate: bool = False
    open_to_remote: bool = True
    travel_willingness: int = 0  # Percentage (0-100)


class SkillSet(BaseModel):
    """Skills with years of experience"""
    all_skills: List[str] = []
    
    # Categorized
    programming_languages: List[str] = []
    frameworks: List[str] = []
    databases: List[str] = []
    cloud_platforms: List[str] = []
    tools: List[str] = []
    
    # Skills with years
    skills_with_years: Dict[str, float] = {}
    
    # Top skills for highlighting
    top_skills: List[str] = []


class Education(BaseModel):
    """Education entry"""
    degree: str
    field_of_study: Optional[str] = None
    institution: str
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None


class Certification(BaseModel):
    """Professional certification"""
    name: str
    issuer: str
    year: Optional[int] = None
    credential_id: Optional[str] = None


class LegalInfo(BaseModel):
    """Legal and work authorization info"""
    work_authorization: WorkAuthorization
    requires_sponsorship: bool = False
    security_clearance: Optional[str] = None
    background_check_ok: bool = True


class SalaryExpectations(BaseModel):
    """Salary expectations"""
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    currency: str = "USD"
    negotiable: bool = True


class Documents(BaseModel):
    """Document paths"""
    resume_path: str
    resume_format: str = "pdf"
    resume_last_updated: datetime = Field(default_factory=datetime.now)
    
    cover_letter_template_path: Optional[str] = None
    portfolio_pdf_path: Optional[str] = None
    references_path: Optional[str] = None


class UserProfile(BaseModel):
    """
    Complete verified user profile
    This is what gets used for job applications
    """
    
    # Profile metadata
    profile_id: str = Field(default_factory=lambda: f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    # Core info
    personal_info: PersonalInfo
    professional_info: ProfessionalInfo
    skills: SkillSet
    education: List[Education] = []
    certifications: List[Certification] = []
    
    # Legal & salary
    legal_info: LegalInfo
    salary_expectations: SalaryExpectations
    
    # Documents
    documents: Documents
    
    # Application preferences
    preferred_job_types: List[JobType] = [JobType.FULL_TIME]
    
    # Resume text (for AI reasoning)
    resume_text: str = ""
    
    def update_timestamp(self):
        """Update last_updated timestamp"""
        self.last_updated = datetime.now()
    
    def get_application_data(self) -> Dict:
        """
        Get data formatted for application forms
        Returns common form fields
        """
        return {
            # Personal
            "first_name": self.personal_info.first_name,
            "last_name": self.personal_info.last_name,
            "full_name": self.personal_info.full_name,
            "email": self.personal_info.email,
            "phone": self.personal_info.phone,
            
            # Location
            "city": self.personal_info.city,
            "state": self.personal_info.state,
            "country": self.personal_info.country,
            "zip_code": self.personal_info.zip_code,
            "location": self.personal_info.location_string,
            
            # Professional
            "current_title": self.professional_info.current_title,
            "current_company": self.professional_info.current_company,
            "years_of_experience": self.professional_info.years_of_experience,
            
            # Links
            "linkedin": str(self.personal_info.linkedin_url) if self.personal_info.linkedin_url else "",
            "github": str(self.personal_info.github_url) if self.personal_info.github_url else "",
            "portfolio": str(self.personal_info.portfolio_url) if self.personal_info.portfolio_url else "",
            
            # Education
            "highest_degree": self.education[0].degree if self.education else "",
            "university": self.education[0].institution if self.education else "",
            "graduation_year": self.education[0].graduation_year if self.education else "",
            
            # Legal
            "work_authorization": self.legal_info.work_authorization.value,
            "require_sponsorship": self.legal_info.requires_sponsorship,
            
            # Availability
            "notice_period": self.professional_info.notice_period,
            "willing_to_relocate": self.professional_info.willing_to_relocate,
            
            # Salary
            "expected_salary_min": self.salary_expectations.min_salary,
            "expected_salary_max": self.salary_expectations.max_salary,
            "salary_currency": self.salary_expectations.currency,
            
            # Documents
            "resume_path": self.documents.resume_path
        }
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: lambda v: str(v)
        }