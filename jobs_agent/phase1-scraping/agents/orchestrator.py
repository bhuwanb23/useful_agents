# agents/orchestrator.py
import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor
from models.job import Job
from models.resume import ResumeAnalysis
from models.preferences import JobPreferences
from scrapers.jobspy_scraper import JobSpyScraper
from scrapers.apify_scraper import ApifyScraper
from scrapers.career_page_scraper import CareerPageScraper
from utils.deduplicator import JobDeduplicator
from tqdm import tqdm

class JobScrapingOrchestrator:
    """
    Coordinates all scraping agents and aggregates results
    """
    
    def __init__(self):
        self.jobspy = JobSpyScraper()
        self.apify = ApifyScraper()
        self.career_scraper = CareerPageScraper()
        self.deduplicator = JobDeduplicator()
    
    async def scrape_all_sources(
        self,
        search_queries: List[str],
        resume_analysis: ResumeAnalysis,
        preferences: JobPreferences,
        career_urls: List[str] = []
    ) -> List[Job]:
        """
        Main orchestration method
        """
        all_jobs = []
        
        print(f"\n🚀 Starting job scraping with {len(search_queries)} queries...")
        print(f"📍 Locations: {preferences.locations or 'Remote'}")
        print(f"🎯 Target: {preferences.results_per_source} jobs per source\n")
        
        # 1. Scrape using JobSpy (multiple queries in parallel)
        print("=" * 60)
        print("🔍 PHASE 1: JobSpy Scraping")
        print("=" * 60)
        
        jobspy_jobs = await self._scrape_with_jobspy(
            search_queries,
            preferences
        )
        all_jobs.extend(jobspy_jobs)
        
        # 2. Scrape using Apify (optional)
        if self.apify.client:
            print("\n" + "=" * 60)
            print("🔍 PHASE 2: Apify Scraping")
            print("=" * 60)
            
            apify_jobs = await self._scrape_with_apify(
                search_queries[:5],  # Limit due to API costs
                preferences
            )
            all_jobs.extend(apify_jobs)
        
        # 3. Scrape career pages
        if career_urls:
            print("\n" + "=" * 60)
            print("🔍 PHASE 3: Career Page Scraping")
            print("=" * 60)
            
            career_jobs = await self._scrape_career_pages(career_urls)
            all_jobs.extend(career_jobs)
        
        # 4. Deduplicate
        print("\n" + "=" * 60)
        print("🧹 PHASE 4: Deduplication")
        print("=" * 60)
        
        print(f"Total jobs before dedup: {len(all_jobs)}")
        unique_jobs = self.deduplicator.deduplicate(all_jobs)
        print(f"✓ Unique jobs: {len(unique_jobs)}")
        print(f"✓ Duplicates removed: {len(all_jobs) - len(unique_jobs)}")
        
        return unique_jobs
    
    async def _scrape_with_jobspy(
        self,
        queries: List[str],
        preferences: JobPreferences
    ) -> List[Job]:
        """Scrape jobs using JobSpy with multiple queries"""
        jobs = []
        
        # Use ThreadPoolExecutor for parallel scraping
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for query in queries[:10]:  # Limit to top 10 queries
                for location in (preferences.locations or [""]):
                    future = executor.submit(
                        self.jobspy.scrape,
                        query=query,
                        location=location,
                        is_remote=preferences.remote_only,
                        results_wanted=preferences.results_per_source,
                        country=preferences.countries[0] if preferences.countries else "USA"
                    )
                    futures.append((query, location, future))
            
            # Collect results with progress bar
            for query, location, future in tqdm(futures, desc="JobSpy queries"):
                try:
                    result = future.result(timeout=60)
                    jobs.extend(result)
                except Exception as e:
                    print(f"✗ Failed: {query} @ {location} - {e}")
        
        return jobs
    
    async def _scrape_with_apify(
        self,
        queries: List[str],
        preferences: JobPreferences
    ) -> List[Job]:
        """Scrape jobs using Apify"""
        jobs = []
        
        for query in tqdm(queries, desc="Apify queries"):
            location = preferences.locations[0] if preferences.locations else ""
            
            # Indeed via Apify
            indeed_jobs = self.apify.scrape_indeed(
                query=query,
                location=location,
                max_items=preferences.results_per_source
            )
            jobs.extend(indeed_jobs)
            
            await asyncio.sleep(2)  # Rate limiting
        
        return jobs
    
    async def _scrape_career_pages(self, career_urls: List[str]) -> List[Job]:
        """Scrape company career pages"""
        jobs = []
        
        for url in tqdm(career_urls, desc="Career pages"):
            try:
                if 'greenhouse' in url:
                    page_jobs = await self.career_scraper.scrape_greenhouse(url)
                elif 'lever' in url:
                    page_jobs = await self.career_scraper.scrape_lever(url)
                else:
                    print(f"⚠️  Unknown career page format: {url}")
                    continue
                
                jobs.extend(page_jobs)
                await asyncio.sleep(3)  # Be respectful
                
            except Exception as e:
                print(f"✗ Error scraping {url}: {e}")
        
        return jobs