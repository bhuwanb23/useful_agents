# scrapers/career_page_scraper.py
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Optional
from models.job import Job
import hashlib
from datetime import datetime
import asyncio

class CareerPageScraper:
    """
    Scrape company career pages directly
    Useful for companies with public job boards
    """
    
    def __init__(self):
        self.name = "career_page"
    
    async def scrape_greenhouse(self, company_url: str) -> List[Job]:
        """
        Scrape Greenhouse-powered career pages
        Format: https://boards.greenhouse.io/company_name
        """
        jobs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(company_url, wait_until="networkidle")
                content = await page.content()
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
                        
                        department = listing.find('span', class_='department')
                        
                        job_id = hashlib.md5(job_url.encode()).hexdigest()[:16]
                        
                        job = Job(
                            job_id=job_id,
                            source="greenhouse",
                            title=title,
                            company=self._extract_company_name(company_url),
                            location=location,
                            is_remote='remote' in (location or '').lower(),
                            description="",  # Would need to visit detail page
                            job_url=job_url,
                            scraped_at=datetime.now()
                        )
                        jobs.append(job)
                    except Exception as e:
                        print(f"Error parsing job: {e}")
                        continue
                
            except Exception as e:
                print(f"Error scraping {company_url}: {e}")
            finally:
                await browser.close()
        
        print(f"✓ Greenhouse found {len(jobs)} jobs")
        return jobs
    
    async def scrape_lever(self, company_url: str) -> List[Job]:
        """
        Scrape Lever-powered career pages
        Format: https://jobs.lever.co/company_name
        """
        # Similar implementation to Greenhouse
        pass
    
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