"""
Application configuration and settings
"""

from pydantic import BaseModel
from typing import List, Dict
from pathlib import Path


class AutomationSettings(BaseModel):
    """Settings for automation behavior"""
    
    # Auto-submit settings
    auto_submit_enabled: bool = False
    auto_submit_for_grades: List[str] = ["A+"]
    review_required_for_grades: List[str] = ["A", "B", "C"]
    skip_grades: List[str] = ["D", "F"]
    
    # Rate limiting
    max_applications_per_day: int = 20
    max_applications_per_hour: int = 5
    delay_between_applications_seconds: int = 60
    
    # Company rules
    same_company_cooldown_days: int = 30
    max_applications_per_company: int = 3


class PlatformLimits(BaseModel):
    """Platform-specific limits"""
    
    linkedin_easy_apply_per_day: int = 50
    indeed_applications_per_day: int = 30
    greenhouse_applications_per_day: int = 100
    rate_limit_delay_seconds: int = 5


class AISettings(BaseModel):
    """AI generation settings"""
    
    generate_cover_letters: bool = True
    cover_letter_tone: str = "professional"  # professional, casual, enthusiastic
    cover_letter_length: str = "medium"       # short, medium, long
    
    answer_screening_questions: bool = True
    screening_confidence_threshold: float = 0.7
    
    ai_model: str = "gemini-pro"


class SafetySettings(BaseModel):
    """Safety and validation settings"""
    
    enable_captcha_detection: bool = True
    pause_on_error: bool = True
    screenshot_on_submit: bool = True
    backup_applications: bool = True
    enable_logging: bool = True
    dry_run_mode: bool = False  # Test without submitting


class NotificationSettings(BaseModel):
    """Notification preferences"""
    
    notify_on_submit: bool = True
    notify_on_error: bool = True
    notify_on_response: bool = True
    
    notification_methods: List[str] = ["console"]  # console, email, slack
    email_notifications_to: str = ""


class ApplicationConfig(BaseModel):
    """Complete application configuration"""
    
    automation: AutomationSettings = AutomationSettings()
    platform_limits: PlatformLimits = PlatformLimits()
    ai_settings: AISettings = AISettings()
    safety: SafetySettings = SafetySettings()
    notifications: NotificationSettings = NotificationSettings()
    
    # Paths
    data_dir: Path = Path("data")
    documents_dir: Path = Path("data/documents")
    screenshots_dir: Path = Path("data/screenshots")
    logs_dir: Path = Path("data/logs")
    
    def ensure_directories(self):
        """Create necessary directories"""
        self.data_dir.mkdir(exist_ok=True)
        self.documents_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)


# Default configuration
DEFAULT_CONFIG = ApplicationConfig()