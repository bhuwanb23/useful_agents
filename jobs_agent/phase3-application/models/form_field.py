"""
Form field models - represents fields in application forms
"""

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class FieldType(str, Enum):
    """HTML input types"""
    TEXT = "text"
    EMAIL = "email"
    TEL = "tel"
    NUMBER = "number"
    DATE = "date"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE = "file"
    HIDDEN = "hidden"


class FieldCategory(str, Enum):
    """What category of data this field asks for"""
    PERSONAL_INFO = "personal_info"
    CONTACT = "contact"
    LOCATION = "location"
    PROFESSIONAL = "professional"
    EDUCATION = "education"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    LEGAL = "legal"
    SALARY = "salary"
    AVAILABILITY = "availability"
    DOCUMENTS = "documents"
    CUSTOM = "custom"


class FormField(BaseModel):
    """
    Represents a field in an application form
    """
    
    # Field identification
    field_id: str  # HTML id or name
    label: str  # Visible label
    placeholder: Optional[str] = None
    hint: Optional[str] = None  # Help text
    
    # Field type
    input_type: FieldType
    field_category: Optional[FieldCategory] = None
    
    # Validation
    required: bool = False
    pattern: Optional[str] = None  # Regex pattern
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # For select/radio
    options: List[str] = []
    
    # Current state
    current_value: Optional[str] = None
    is_filled: bool = False
    
    # Matching
    matched_to: Optional[str] = None  # e.g., "user_profile.personal_info.email"
    confidence: float = 0.0  # How confident we are in the match
    
    # Metadata
    selector: Optional[str] = None  # CSS/XPath selector
    parent_form: Optional[str] = None
    step_number: Optional[int] = None  # For multi-step forms
    
    @property
    def is_simple(self) -> bool:
        """Can this field be auto-filled easily?"""
        return self.input_type in [FieldType.TEXT, FieldType.EMAIL, FieldType.TEL]
    
    @property
    def needs_ai(self) -> bool:
        """Does this field need AI to answer?"""
        return self.input_type == FieldType.TEXTAREA or self.field_category == FieldCategory.CUSTOM


class DetectedForm(BaseModel):
    """
    A complete detected form
    """
    form_id: str
    form_url: str
    form_title: Optional[str] = None
    
    fields: List[FormField] = []
    
    # Multi-step detection
    is_multi_step: bool = False
    total_steps: int = 1
    current_step: int = 1
    
    # Complexity
    total_fields: int = 0
    required_fields: int = 0
    auto_fillable_fields: int = 0
    ai_required_fields: int = 0
    manual_required_fields: int = 0
    
    # Estimated time
    estimated_time_seconds: int = 0
    
    @property
    def automation_rate(self) -> float:
        """What percentage can be auto-filled?"""
        if self.total_fields == 0:
            return 0.0
        return self.auto_fillable_fields / self.total_fields
    
    @property
    def complexity(self) -> str:
        """Easy, Medium, Hard"""
        if self.total_fields <= 10 and self.automation_rate >= 0.8:
            return "easy"
        elif self.total_fields <= 20 and self.automation_rate >= 0.5:
            return "medium"
        else:
            return "hard"