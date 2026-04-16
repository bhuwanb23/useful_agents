"""
Patterns for detecting and matching form fields
"""

from typing import Dict, List

# Field matching patterns
# Format: field_type -> list of keywords/patterns

FIELD_PATTERNS: Dict[str, List[str]] = {
    # Personal Info
    "first_name": [
        "first name", "given name", "fname", "first_name",
        "forename", "christian name"
    ],
    "last_name": [
        "last name", "surname", "family name", "lname", "last_name"
    ],
    "full_name": [
        "full name", "name", "your name", "full_name",
        "legal name", "complete name"
    ],
    "email": [
        "email", "e-mail", "email address", "e-mail address",
        "contact email", "work email", "personal email"
    ],
    "phone": [
        "phone", "telephone", "mobile", "cell", "phone number",
        "contact number", "mobile number", "tel"
    ],
    
    # Location
    "city": [
        "city", "town", "municipality"
    ],
    "state": [
        "state", "province", "region"
    ],
    "country": [
        "country", "nation", "nationality"
    ],
    "zip_code": [
        "zip", "zip code", "postal code", "postcode", "pincode"
    ],
    "address": [
        "address", "street address", "home address",
        "residential address", "mailing address"
    ],
    
    # Professional
    "current_title": [
        "current title", "job title", "position", "role",
        "current position", "current role"
    ],
    "current_company": [
        "current company", "employer", "current employer",
        "organization", "company name"
    ],
    "years_of_experience": [
        "years of experience", "years experience", "total experience",
        "work experience", "professional experience", "experience years"
    ],
    "years_in_role": [
        "years in role", "years in position", "time in role"
    ],
    
    # Links
    "linkedin": [
        "linkedin", "linkedin profile", "linkedin url",
        "linkedin.com", "linkedin link"
    ],
    "github": [
        "github", "github profile", "github username",
        "github.com", "github link"
    ],
    "portfolio": [
        "portfolio", "portfolio website", "portfolio url",
        "personal website", "website", "portfolio link"
    ],
    
    # Education
    "degree": [
        "degree", "highest degree", "education level",
        "qualification", "diploma"
    ],
    "university": [
        "university", "college", "school", "institution",
        "educational institution"
    ],
    "graduation_year": [
        "graduation year", "year graduated", "graduation date",
        "completion year", "year of graduation"
    ],
    "gpa": [
        "gpa", "grade point average", "grades", "cgpa"
    ],
    
    # Work Authorization
    "work_authorization": [
        "work authorization", "authorized to work", "work permit",
        "visa status", "work eligibility", "employment authorization"
    ],
    "require_sponsorship": [
        "sponsorship", "require sponsorship", "need sponsorship",
        "visa sponsorship", "h1b sponsorship"
    ],
    
    # Salary
    "salary_expectation": [
        "salary", "expected salary", "salary expectation",
        "compensation", "pay", "salary requirements",
        "desired salary", "target salary"
    ],
    "current_salary": [
        "current salary", "current compensation",
        "present salary", "existing salary"
    ],
    
    # Availability
    "start_date": [
        "start date", "available to start", "when can you start",
        "availability", "earliest start date", "notice period"
    ],
    "notice_period": [
        "notice period", "notice required", "how much notice",
        "resignation notice"
    ],
    
    # Relocation
    "willing_to_relocate": [
        "relocate", "relocation", "willing to relocate",
        "open to relocation", "can you relocate"
    ],
    
    # Experience with specific skills
    "skill_years": [
        "years of", "experience with", "years with",
        "how long", "how many years"
    ],
    
    # Documents
    "resume_upload": [
        "resume", "cv", "curriculum vitae", "upload resume",
        "attach resume", "resume file"
    ],
    "cover_letter_upload": [
        "cover letter", "letter of interest", "upload cover letter",
        "motivation letter"
    ],
    
    # Yes/No questions
    "yes_no": [
        "are you", "do you", "have you", "can you", "will you"
    ]
}


# Patterns for detecting question types
QUESTION_TYPE_PATTERNS: Dict[str, List[str]] = {
    "work_authorization": [
        "authorized to work", "work authorization", "visa status",
        "require sponsorship", "work permit", "employment eligibility"
    ],
    "salary": [
        "salary", "compensation", "expected pay", "salary range",
        "salary requirements", "desired salary"
    ],
    "years_experience": [
        "years of experience", "how many years", "total experience",
        "years experience", "experience level"
    ],
    "availability": [
        "when can you start", "start date", "available to start",
        "notice period", "availability"
    ],
    "relocation": [
        "willing to relocate", "relocation", "can you relocate",
        "open to relocation"
    ],
    "motivation": [
        "why do you want", "why are you interested", "what interests you",
        "why this company", "why this role"
    ]
}


# Common dropdown options
DROPDOWN_OPTIONS: Dict[str, List[str]] = {
    "work_authorization": [
        "US Citizen",
        "Green Card Holder",
        "H1B Visa",
        "OPT (F1)",
        "Require Sponsorship",
        "Other"
    ],
    "education_level": [
        "High School",
        "Associate Degree",
        "Bachelor's Degree",
        "Master's Degree",
        "PhD",
        "Professional Degree"
    ],
    "experience_level": [
        "Entry Level",
        "Junior",
        "Mid-Level",
        "Senior",
        "Lead",
        "Principal"
    ],
    "notice_period": [
        "Immediately",
        "1 week",
        "2 weeks",
        "1 month",
        "2 months",
        "3+ months"
    ]
}


def match_field_to_pattern(field_label: str) -> str:
    """
    Match a field label to a pattern
    Returns the field type or "unknown"
    """
    field_label_lower = field_label.lower().strip()
    
    for field_type, patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            if pattern in field_label_lower:
                return field_type
    
    return "unknown"


def detect_question_type(question_text: str) -> str:
    """
    Detect the type of question being asked
    """
    question_lower = question_text.lower().strip()
    
    for q_type, patterns in QUESTION_TYPE_PATTERNS.items():
        for pattern in patterns:
            if pattern in question_lower:
                return q_type
    
    return "custom"