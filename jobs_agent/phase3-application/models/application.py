"""
Application model - tracks job applications
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    """Application status"""
    PREPARED = "prepared"          # Ready to submit
    SUBMITTED = "submitted"        # Application sent
    CONFIRMED = "confirmed"        # Got confirmation email
    UNDER_REVIEW = "under_review"  # Being reviewed
    INTERVIEW = "interview"        # Interview scheduled
    OFFER = "offer"                # Got offer!
    REJECTED = "rejected"          # Rejected
    WITHDRAWN = "withdrawn"        # User withdrew
    GHOSTED = "ghosted"            # No response after 30+ days


class ApplicationMethod(str, Enum):
    """How the application was submitted"""
    LINKEDIN_EASY_APPLY = "linkedin_easy_apply"
    INDEED_QUICK_APPLY = "indeed_quick_apply"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKDAY = "workday"
    EMAIL = "email"
    CUSTOM_FORM = "custom_form"
    MANUAL = "manual"


class ScreeningQuestion(BaseModel):
    """A screening question and answer"""
    question_text: str
    answer_text: str
    answer_strategy: str  # auto, ai, manual
    confidence: float = 1.0
    was_edited: bool = False


class Application(BaseModel):
    """
    Complete application record
    """
    
    # Application ID
    application_id: str = Field(default_factory=lambda: f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Job details
    job_id: str  # Links to scored_jobs
    company: str
    title: str
    job_url: HttpUrl
    match_score: float
    grade: str  # A+, A, B, etc.
    
    # Application details
    application_method: ApplicationMethod
    application_url: Optional[HttpUrl] = None
    
    # Status
    status: ApplicationStatus = ApplicationStatus.PREPARED
    applied_date: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Content
    cover_letter_text: str = ""
    cover_letter_path: Optional[str] = None
    resume_used: str = ""  # Path to resume used
    
    # Screening questions
    screening_questions: List[ScreeningQuestion] = []
    
    # Submission details
    submission_time_seconds: Optional[float] = None
    submission_screenshot_path: Optional[str] = None
    
    # Tracking
    confirmation_email_received: bool = False
    confirmation_code: Optional[str] = None
    interview_date: Optional[datetime] = None
    
    # Notes
    user_notes: str = ""
    error_log: str = ""
    
    # Analytics
    preparation_time_seconds: Optional[float] = None
    review_time_seconds: Optional[float] = None
    
    def mark_submitted(self):
        """Mark as submitted"""
        self.status = ApplicationStatus.SUBMITTED
        self.applied_date = datetime.now()
        self.last_updated = datetime.now()
    
    def mark_confirmed(self, confirmation_code: str = None):
        """Mark as confirmed"""
        self.status = ApplicationStatus.CONFIRMED
        self.confirmation_email_received = True
        self.confirmation_code = confirmation_code
        self.last_updated = datetime.now()
    
    def update_status(self, new_status: ApplicationStatus, notes: str = ""):
        """Update status"""
        self.status = new_status
        self.last_updated = datetime.now()
        if notes:
            self.user_notes += f"\n[{datetime.now()}] {notes}"
    
    @property
    def days_since_applied(self) -> Optional[int]:
        """Days since application was submitted"""
        if not self.applied_date:
            return None
        return (datetime.now() - self.applied_date).days
    
    @property
    def is_ghosted(self) -> bool:
        """Has it been too long without response?"""
        if self.status in [ApplicationStatus.SUBMITTED, ApplicationStatus.CONFIRMED]:
            days = self.days_since_applied
            return days and days > 30
        return False


class ApplicationEvent(BaseModel):
    """An event in the application lifecycle"""
    event_id: str = Field(default_factory=lambda: f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    application_id: str
    event_type: str  # form_filled, document_uploaded, submitted, etc.
    event_data: Dict = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None