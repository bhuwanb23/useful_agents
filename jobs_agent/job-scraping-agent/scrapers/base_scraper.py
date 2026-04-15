# scrapers/base_scraper.py
from abc import ABC, abstractmethod
from typing import List, Optional
from models.job import Job
import time
import random

class BaseScraper(ABC):
    """
    Abstract base class for all scrapers
    Provides common functionality and interface
    """
    
    def __init__(self, name: str):
        self.name = name
        self.jobs_scraped = 0
        self.errors = 0
    
    @abstractmethod
    def scrape(self, query: str, **kwargs) -> List[Job]:
        """
        Main scraping method - must be implemented by subclasses
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            List of Job objects
        """
        pass
    
    def rate_limit(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """
        Add random delay to avoid rate limiting
        """
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def log_scrape(self, query: str, job_count: int, success: bool = True):
        """
        Log scraping activity
        """
        status = "✓" if success else "✗"
        print(f"{status} [{self.name}] Query: '{query}' - Found: {job_count} jobs")
        
        if success:
            self.jobs_scraped += job_count
        else:
            self.errors += 1
    
    def get_stats(self) -> dict:
        """
        Get scraper statistics
        """
        return {
            "name": self.name,
            "jobs_scraped": self.jobs_scraped,
            "errors": self.errors
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.jobs_scraped = 0
        self.errors = 0
    
    def validate_job(self, job: Job) -> bool:
        """
        Validate job data before returning
        """
        required_fields = ['title', 'company', 'job_url']
        
        for field in required_fields:
            if not getattr(job, field, None):
                print(f"⚠️  Invalid job: missing {field}")
                return False
        
        return True
    
    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """
        Clean and normalize text
        """
        if not text:
            return None
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters
        text = text.strip()
        
        return text if text else None