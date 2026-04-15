# scrapers/apify_scraper.py
from apify_client import ApifyClient
from typing import List, Optional
from models.job import Job
from config.settings import settings
import hashlib
from datetime import datetime

class ApifyScraper:
    """
    Uses Apify actors for scraping
    Free tier: $5 credit/month
    """
    
    def __init__(self):
        if not settings.APIFY_API_KEY:
            print("⚠️  Apify API key not set, skipping Apify scraper")
            self.client = None
            return
        
        self.client = ApifyClient(settings.APIFY_API_KEY)
        self.name = "apify"
    
    def scrape_indeed(
        self,
        query: str,
        location: str = "",
        max_items: int = 50
    ) -> List[Job]:
        """
        Scrape Indeed using Apify actor
        Actor: https://apify.com/misceres/indeed-scraper
        """
        if not self.client:
            return []
        
        try:
            run_input = {
                "position": query,
                "location": location,
                "maxItems": max_items,
                "parseCompanyDetails": False,
            }
            
            # Run actor
            run = self.client.actor("misceres/indeed-scraper").call(run_input=run_input)
            
            # Get results
            jobs = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                job = self._item_to_job(item, "indeed")
                if job:
                    jobs.append(job)
            
            print(f"✓ Apify-Indeed found {len(jobs)} jobs for '{query}'")
            return jobs
            
        except Exception as e:
            print(f"✗ Apify-Indeed error: {e}")
            return []
    
    def scrape_linkedin(
        self,
        query: str,
        location: str = "",
        max_items: int = 50
    ) -> List[Job]:
        """
        LinkedIn scraper - use cautiously (may require proxies)
        """
        # Implementation similar to Indeed
        # Actor: "voyager/linkedin-jobs-scraper"
        pass
    
    def _item_to_job(self, item: dict, source: str) -> Optional[Job]:
        """Convert Apify item to Job model"""
        try:
            job_id = hashlib.md5(
                f"{item.get('url', '')}{item.get('title', '')}".encode()
            ).hexdigest()[:16]
            
            return Job(
                job_id=job_id,
                source=f"apify_{source}",
                title=item.get('title', 'Unknown'),
                company=item.get('company', 'Unknown'),
                location=item.get('location'),
                is_remote='remote' in item.get('location', '').lower(),
                description=item.get('description', ''),
                job_url=item.get('url', 'https://example.com'),
                salary_min=item.get('salary', {}).get('min'),
                salary_max=item.get('salary', {}).get('max'),
                scraped_at=datetime.now()
            )
        except Exception as e:
            print(f"Error converting Apify item: {e}")
            return None