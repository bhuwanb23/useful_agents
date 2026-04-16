
"""
Data models for Phase 3
"""

from .extracted_profile import (
    ExtractedProfile,
    ExtractedPersonalInfo,
    ExtractedProfessionalInfo,
    ExtractedSkills,
    ExtractedEducationInfo,
    ExtractedField,
    ExtractionSource,
    ConfidenceLevel
)

from .user_profile import (
    UserProfile,
    PersonalInfo,
    ProfessionalInfo,
    SkillSet,
    Education,
    LegalInfo,
    SalaryExpectations,
    WorkAuthorization
)

from .learned_question import (
    LearnedQuestion,
    QuestionDatabase,
    QuestionType,
    AnswerStrategy
)

from .application import (
    Application,
    ApplicationEvent,
    ApplicationStatus,
    ApplicationMethod,
    ScreeningQuestion
)

from .form_field import (
    FormField,
    DetectedForm,
    FieldType,
    FieldCategory
)

__all__ = [
    # Extracted Profile
    'ExtractedProfile',
    'ExtractedPersonalInfo',
    'ExtractedProfessionalInfo',
    'ExtractedSkills',
    'ExtractedField',
    
    # User Profile
    'UserProfile',
    'PersonalInfo',
    'ProfessionalInfo',
    'SkillSet',
    'Education',
    
    # Questions
    'LearnedQuestion',
    'QuestionDatabase',
    
    # Applications
    'Application',
    'ApplicationEvent',
    
    # Form Fields
    'FormField',
    'DetectedForm'
]