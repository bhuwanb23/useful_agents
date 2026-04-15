# scrapers/career_page_scraper.py
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Optional
from models.job import Job
import hashlib
from datetime import datetime
import asyncio
import requests

class CareerPageScraper:
    """
    Scrape company career pages directly
    Useful for companies with public job boards
    """
    
    def __init__(self):
        self.name = "career_page"
        self.playwright_available = True
    
    async def scrape_greenhouse(self, company_url: str) -> List[Job]:
        """
        Scrape Greenhouse-powered career pages
        Format: https://boards.greenhouse.io/company_name
        """
        jobs = []
        
        # Try Playwright first, fallback to requests
        try:
            jobs = await self._scrape_with_playwright(company_url, 'greenhouse')
        except Exception as e:
            if 'Executable doesn' in str(e) or 'playwright' in str(e).lower():
                print(f"⚠️  Playwright not available, using HTTP fallback for {company_url}")
                jobs = self._scrape_greenhouse_http(company_url)
            else:
                print(f"Error scraping {company_url}: {e}")
        
        print(f"✓ Greenhouse found {len(jobs)} jobs")
        return jobs
    
    async def _scrape_with_playwright(self, company_url: str, platform: str) -> List[Job]:
        """Scrape using Playwright (browser automation)"""
        jobs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(company_url, wait_until="networkidle")
                content = await page.content()
                
                if platform == 'greenhouse':
                    jobs = self._parse_greenhouse_content(content, company_url)
                
            finally:
                await browser.close()
        
        return jobs
    
    def _scrape_greenhouse_http(self, company_url: str) -> List[Job]:
        """Fallback: Scrape Greenhouse using simple HTTP requests"""
        jobs = []
        
        try:
            # Greenhouse has a JSON API
            # Extract company name from URL
            company_name = self._extract_company_name(company_url)
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{company_name}/jobs?content=false"
            
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse jobs from API response
            for job_data in data.get('jobs', []):
                try:
                    job_id = hashlib.md5(
                        f"{job_data.get('absolute_url', '')}".encode()
                    ).hexdigest()[:16]
                    
                    location = job_data.get('location', {}).get('name', '')
                    
                    job = Job(
                        job_id=job_id,
                        source="greenhouse",
                        title=job_data.get('title', 'Unknown'),
                        company=company_name,
                        location=location,
                        is_remote='remote' in location.lower() if location else False,
                        description=job_data.get('description', ''),
                        job_url=job_data.get('absolute_url', company_url),
                        scraped_at=datetime.now()
                    )
                    jobs.append(job)
                except Exception as e:
                    print(f"Error parsing job: {e}")
                    continue
            
        except Exception as e:
            print(f"✗ HTTP fallback failed for {company_url}: {e}")
        
        return jobs
    
    def _parse_greenhouse_content(self, content: str, company_url: str) -> List[Job]:
        """Parse Greenhouse HTML content"""
        jobs = []
        soup = BeautifulSoup(content, 'html.parser')
        
        # Greenhouse specific selectors
        job_listings = soup.find_all('div', class_='opening')
        
        for listing in job_listings:
            try:
                title_elem = listing.find('a')
                title = title_elem.text.strip()
                job_url = title_elem['href']
                
                if not job_url.startswith('http'):
                    job_url = f"https://boards.greenhouse.io{job_url}"
                
                location_elem = listing.find('span', class_='location')
                location = location_elem.text.strip() if location_elem else None
                
                job_id = hashlib.md5(job_url.encode()).hexdigest()[:16]
                
                job = Job(
                    job_id=job_id,
                    source="greenhouse",
                    title=title,
                    company=self._extract_company_name(company_url),
                    location=location,
                    is_remote='remote' in (location or '').lower(),
                    description="",
                    job_url=job_url,
                    scraped_at=datetime.now()
                )
                jobs.append(job)
            except Exception as e:
                print(f"Error parsing job: {e}")
                continue
        
        return jobs
    
    async def scrape_lever(self, company_url: str) -> List[Job]:
        """
        Scrape Lever-powered career pages
        Format: https://jobs.lever.co/company_name
        """
        jobs = []
        
        try:
            # Lever has a JSON API
            company_name = self._extract_company_name(company_url)
            api_url = f"https://api.lever.co/v0/postings/{company_name}?mode=json"
            
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            for job_data in data:
                try:
                    job_id = hashlib.md5(
                        f"{job_data.get('hostedUrl', '')}".encode()
                    ).hexdigest()[:16]
                    
                    location = job_data.get('categories', {}).get('location', '')
                    
                    job = Job(
                        job_id=job_id,
                        source="lever",
                        title=job_data.get('text', 'Unknown'),
                        company=company_name,
                        location=location,
                        is_remote='remote' in location.lower() if location else False,
                        description=job_data.get('description', {}).get('content', ''),
                        job_url=job_data.get('hostedUrl', company_url),
                        scraped_at=datetime.now()
                    )
                    jobs.append(job)
                except Exception as e:
                    print(f"Error parsing Lever job: {e}")
                    continue
            
        except Exception as e:
            print(f"✗ Error scraping Lever {company_url}: {e}")
        
        print(f"✓ Lever found {len(jobs)} jobs")
        return jobs
    
    async def scrape_workday(self, company_url: str) -> List[Job]:
        """
        Scrape Workday career pages (more complex)
        """
        # Workday uses dynamic loading, need to handle AJAX
        pass
    
    def _extract_company_name(self, url: str) -> str:
        """Extract company name from URL"""
        parts = url.rstrip('/').split('/')
        return parts[-1].replace('-', ' ').title()

# Usage example
"""
async def main():
    scraper = CareerPageScraper()
    jobs = await scraper.scrape_greenhouse("https://boards.greenhouse.io/openai")
    print(f"Found {len(jobs)} jobs")

asyncio.run(main())
"""