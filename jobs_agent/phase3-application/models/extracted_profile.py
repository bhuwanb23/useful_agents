"""
Data models for AI-extracted profile information.
Each field includes the extracted value, confidence score, and source.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence levels for extracted data"""
    HIGH = "high"      # 90-100% - Auto-accept
    MEDIUM = "medium"  # 70-89% - Review recommended
    LOW = "low"        # 50-69% - User verification required
    NONE = "none"      # 0-49% - Missing/unreliable


class ExtractionSource(str, Enum):
    """Where the data was extracted from"""
    RESUME_HEADER = "resume_header"
    RESUME_CONTACT = "resume_contact"
    RESUME_SUMMARY = "resume_summary"
    RESUME_EXPERIENCE = "resume_experience"
    RESUME_SKILLS = "resume_skills"
    RESUME_EDUCATION = "resume_education"
    RESUME_CERTIFICATIONS = "resume_certifications"
    RESUME_LINKS = "resume_links"
    AI_INFERENCE = "ai_inference"
    CALCULATED = "calculated"
    NOT_FOUND = "not_found"


class ExtractedField(BaseModel):
    """
    Base model for any extracted field with confidence tracking
    """
    value: Optional[Any] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)  # 0.0 to 1.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.NONE
    source: ExtractionSource = ExtractionSource.NOT_FOUND
    extraction_method: str = "unknown"  # "regex", "ai", "calculated"
    reasoning: Optional[str] = None  # Why AI chose this value
    needs_review: bool = True
    alternative_values: List[Any] = []  # Other possible values AI found
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-set confidence level based on confidence score
        if self.confidence >= 0.90:
            self.confidence_level = ConfidenceLevel.HIGH
            self.needs_review = False
        elif self.confidence >= 0.70:
            self.confidence_level = ConfidenceLevel.MEDIUM
            self.needs_review = True
        elif self.confidence >= 0.50:
            self.confidence_level = ConfidenceLevel.LOW
            self.needs_review = True
        else:
            self.confidence_level = ConfidenceLevel.NONE
            self.needs_review = True
    
    @property
    def is_confident(self) -> bool:
        """Is this field confident enough to use without review?"""
        return self.confidence >= 0.90
    
    @property
    def has_value(self) -> bool:
        """Does this field have a value?"""
        return self.value is not None and self.value != ""


class ExtractedPersonalInfo(BaseModel):
    """Personal information extracted from resume"""
    
    first_name: ExtractedField = Field(default_factory=ExtractedField)
    last_name: ExtractedField = Field(default_factory=ExtractedField)
    full_name: ExtractedField = Field(default_factory=ExtractedField)
    
    email: ExtractedField = Field(default_factory=ExtractedField)
    phone: ExtractedField = Field(default_factory=ExtractedField)
    
    # Location
    city: ExtractedField = Field(default_factory=ExtractedField)
    state: ExtractedField = Field(default_factory=ExtractedField)
    country: ExtractedField = Field(default_factory=ExtractedField)
    zip_code: ExtractedField = Field(default_factory=ExtractedField)
    full_address: ExtractedField = Field(default_factory=ExtractedField)
    
    # Social links
    linkedin_url: ExtractedField = Field(default_factory=ExtractedField)
    github_url: ExtractedField = Field(default_factory=ExtractedField)
    portfolio_url: ExtractedField = Field(default_factory=ExtractedField)
    twitter_url: ExtractedField = Field(default_factory=ExtractedField)
    
    @property
    def review_required_fields(self) -> List[str]:
        """List of fields that need user review"""
        return [
            name for name, field in self.__dict__.items()
            if isinstance(field, ExtractedField) and field.needs_review
        ]


class ExtractedProfessionalInfo(BaseModel):
    """Professional information extracted from resume"""
    
    current_title: ExtractedField = Field(default_factory=ExtractedField)
    current_company: ExtractedField = Field(default_factory=ExtractedField)
    
    years_of_experience: ExtractedField = Field(default_factory=ExtractedField)
    seniority_level: ExtractedField = Field(default_factory=ExtractedField)
    
    # Will be filled from resume analysis (Phase 1/2)
    job_titles: ExtractedField = Field(default_factory=ExtractedField)  # List
    industries: ExtractedField = Field(default_factory=ExtractedField)   # List
    
    # Inferred data
    notice_period: ExtractedField = Field(default_factory=ExtractedField)
    willing_to_relocate: ExtractedField = Field(default_factory=ExtractedField)
    open_to_remote: ExtractedField = Field(default_factory=ExtractedField)


class SkillWithYears(BaseModel):
    """A skill with years of experience"""
    skill_name: str
    years: float
    confidence: float
    source: str  # Where we found evidence of this skill
    
    
class ExtractedSkills(BaseModel):
    """Skills extracted from resume"""
    
    # All skills (flat list)
    all_skills: ExtractedField = Field(default_factory=ExtractedField)  # List[str]
    
    # Categorized skills
    programming_languages: ExtractedField = Field(default_factory=ExtractedField)
    frameworks: ExtractedField = Field(default_factory=ExtractedField)
    databases: ExtractedField = Field(default_factory=ExtractedField)
    cloud_platforms: ExtractedField = Field(default_factory=ExtractedField)
    tools: ExtractedField = Field(default_factory=ExtractedField)
    
    # Skills with years of experience
    skills_with_years: Dict[str, SkillWithYears] = {}
    
    # Top skills (prioritized)
    top_skills: List[str] = []


class ExtractedEducation(BaseModel):
    """Single education entry"""
    degree: str
    field_of_study: Optional[str] = None
    institution: str
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    location: Optional[str] = None
    confidence: float = 0.0


class ExtractedEducationInfo(BaseModel):
    """Education information extracted from resume"""
    
    highest_degree: ExtractedField = Field(default_factory=ExtractedField)
    field_of_study: ExtractedField = Field(default_factory=ExtractedField)
    institution: ExtractedField = Field(default_factory=ExtractedField)
    graduation_year: ExtractedField = Field(default_factory=ExtractedField)
    
    # All education entries
    all_education: List[ExtractedEducation] = []


class ExtractedCertification(BaseModel):
    """Single certification"""
    name: str
    issuer: Optional[str] = None
    year: Optional[int] = None
    confidence: float = 0.0


class ExtractedLegalInfo(BaseModel):
    """Legal/work authorization info (usually NOT in resume, needs user input)"""
    
    work_authorization: ExtractedField = Field(default_factory=ExtractedField)
    requires_sponsorship: ExtractedField = Field(default_factory=ExtractedField)
    security_clearance: ExtractedField = Field(default_factory=ExtractedField)


class ExtractedSalaryInfo(BaseModel):
    """Salary expectations (usually NOT in resume, needs user input)"""
    
    min_salary: ExtractedField = Field(default_factory=ExtractedField)
    max_salary: ExtractedField = Field(default_factory=ExtractedField)
    currency: ExtractedField = Field(default_factory=ExtractedField)


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process"""
    
    extracted_at: datetime = Field(default_factory=datetime.now)
    resume_source: str  # Path to resume file
    resume_format: str  # "markdown", "pdf", etc.
    ai_model: str = "gemini-pro"
    extraction_version: str = "1.0.0"
    
    # Overall quality metrics
    overall_confidence: float = 0.0
    total_fields_extracted: int = 0
    high_confidence_fields: int = 0
    medium_confidence_fields: int = 0
    low_confidence_fields: int = 0
    missing_fields: int = 0
    
    # Processing info
    extraction_time_seconds: float = 0.0
    ai_tokens_used: int = 0
    errors_encountered: List[str] = []


class ExtractedProfile(BaseModel):
    """
    Complete AI-extracted profile from resume
    This is the OUTPUT of resume extraction
    """
    
    metadata: ExtractionMetadata
    
    personal_info: ExtractedPersonalInfo = Field(default_factory=ExtractedPersonalInfo)
    professional_info: ExtractedProfessionalInfo = Field(default_factory=ExtractedProfessionalInfo)
    skills: ExtractedSkills = Field(default_factory=ExtractedSkills)
    education: ExtractedEducationInfo = Field(default_factory=ExtractedEducationInfo)
    
    certifications: List[ExtractedCertification] = []
    
    legal_info: ExtractedLegalInfo = Field(default_factory=ExtractedLegalInfo)
    salary_info: ExtractedSalaryInfo = Field(default_factory=ExtractedSalaryInfo)
    
    # Raw resume text (for AI reasoning later)
    raw_resume_text: str = ""
    
    def get_review_summary(self) -> Dict[str, Any]:
        """
        Get summary of what needs review
        """
        return {
            "total_fields": self.metadata.total_fields_extracted,
            "needs_review": self.metadata.medium_confidence_fields + 
                          self.metadata.low_confidence_fields + 
                          self.metadata.missing_fields,
            "high_confidence": self.metadata.high_confidence_fields,
            "overall_confidence": f"{self.metadata.overall_confidence * 100:.1f}%",
            "ready_to_use": self.metadata.overall_confidence >= 0.80
        }
    
    def get_all_review_fields(self) -> Dict[str, List[str]]:
        """
        Get all fields that need review, categorized
        """
        review_fields = {
            "high_priority": [],  # Low confidence or missing
            "medium_priority": [],  # Medium confidence
            "optional": []  # Low confidence but not critical
        }
        
        # Check all sections
        sections = [
            ("personal_info", self.personal_info),
            ("professional_info", self.professional_info),
            ("education", self.education)
        ]
        
        for section_name, section in sections:
            for field_name, field in section.__dict__.items():
                if isinstance(field, ExtractedField):
                    if field.needs_review:
                        if field.confidence_level == ConfidenceLevel.NONE:
                            review_fields["high_priority"].append(f"{section_name}.{field_name}")
                        elif field.confidence_level == ConfidenceLevel.LOW:
                            review_fields["high_priority"].append(f"{section_name}.{field_name}")
                        else:  # MEDIUM
                            review_fields["medium_priority"].append(f"{section_name}.{field_name}")
        
        return review_fields
    
    def to_json_summary(self) -> str:
        """
        Export as readable JSON summary
        """
        import json
        
        summary = {
            "extraction_date": self.metadata.extracted_at.isoformat(),
            "overall_confidence": f"{self.metadata.overall_confidence * 100:.1f}%",
            "personal_info": {
                "name": self.personal_info.full_name.value,
                "email": self.personal_info.email.value,
                "phone": self.personal_info.phone.value,
                "location": f"{self.personal_info.city.value}, {self.personal_info.state.value}"
                           if self.personal_info.city.value else None
            },
            "professional": {
                "current_title": self.professional_info.current_title.value,
                "current_company": self.professional_info.current_company.value,
                "years_experience": self.professional_info.years_of_experience.value
            },
            "skills": self.skills.top_skills[:10] if self.skills.top_skills else [],
            "education": {
                "degree": self.education.highest_degree.value,
                "institution": self.education.institution.value
            },
            "needs_review": self.get_all_review_fields()
        }
        
        return json.dumps(summary, indent=2, default=str)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Helper functions for creating ExtractedFields quickly

def create_extracted_field(
    value: Any,
    confidence: float,
    source: ExtractionSource,
    method: str = "ai",
    reasoning: str = None
) -> ExtractedField:
    """
    Helper to create ExtractedField with proper confidence level
    """
    return ExtractedField(
        value=value,
        confidence=confidence,
        source=source,
        extraction_method=method,
        reasoning=reasoning
    )


def create_high_confidence_field(
    value: Any,
    source: ExtractionSource,
    reasoning: str = None
) -> ExtractedField:
    """
    Create a high-confidence field (90%+)
    """
    return create_extracted_field(
        value=value,
        confidence=0.95,
        source=source,
        method="regex" if source != ExtractionSource.AI_INFERENCE else "ai",
        reasoning=reasoning
    )


def create_missing_field() -> ExtractedField:
    """
    Create a field for missing data
    """
    return ExtractedField(
        value=None,
        confidence=0.0,
        source=ExtractionSource.NOT_FOUND,
        extraction_method="none",
        reasoning="Not found in resume",
        needs_review=True
    )