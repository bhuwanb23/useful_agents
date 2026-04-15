# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # AI API Keys (Use FREE Gemini!)
    GOOGLE_API_KEY: str  # Get from Google AI Studio - FREE
    OPENAI_API_KEY: Optional[str] = None  # Optional
    
    # Apify (Free tier: 5 actors, $5 credit/month)
    APIFY_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///data/jobs.db"
    
    # Scraping Settings
    MAX_CONCURRENT_SCRAPERS: int = 5
    REQUEST_DELAY: int = 2  # seconds
    MAX_JOBS_PER_SOURCE: int = 100
    
    # Job Preferences (defaults)
    DEFAULT_COUNTRY: str = "USA"
    DEFAULT_RESULTS_WANTED: int = 50
    
    class Config:
        env_file = ".env"

settings = Settings()