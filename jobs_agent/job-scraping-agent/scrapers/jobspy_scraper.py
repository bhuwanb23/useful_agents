# scrapers/jobspy_scraper.py
from jobspy import scrape_jobs
from typing import List
import pandas as pd
from models.job import Job, JobType
from datetime import datetime
import hashlib

class JobSpyScraper:
    """
    Wrapper around python-jobspy library
    Supports: Indeed, LinkedIn, ZipRecruiter, Glassdoor, Google
    """
    
    # Note: Only these sites are supported in JobSpy v1.1.13
    # Glassdoor and Google removed due to API issues
    # Reference: https://github.com/Credence-Technologies/python-jobspy
    SUPPORTED_SITES = ["indeed", "linkedin", "zip_recruiter"]
    
    def __init__(self):
        self.name = "jobspy"
    
    def scrape(
        self,
        query: str,
        location: str = "",
        distance: int = 50,
        is_remote: bool = False,
        results_wanted: int = 50,
        country: str = "USA"
    ) -> List[Job]:
        """
        Scrape jobs using JobSpy
        """
        try:
            # JobSpy scrape
            # Reference: https://github.com/Credence-Technologies/python-jobspy
            # Note: hours_old not supported in v1.1.13, using default time filtering
            jobs_df = scrape_jobs(
                site_name=self.SUPPORTED_SITES,  # Search all sites
                search_term=query,
                location=location if location else None,
                distance=distance,
                is_remote=is_remote,
                results_wanted=results_wanted,
                country_indeed=country
            )
            
            if jobs_df is None or jobs_df.empty:
                print(f"No jobs found for query: {query}")
                return []
            
            # Convert to Job models
            jobs = []
            for _, row in jobs_df.iterrows():
                job = self._df_row_to_job(row)
                if job:
                    jobs.append(job)
            
            print(f"✓ JobSpy found {len(jobs)} jobs for '{query}'")
            return jobs
            
        except Exception as e:
            error_msg = str(e)
            # Common JobSpy errors
            if '403' in error_msg or 'blocked' in error_msg.lower():
                print(f"⚠️  JobSpy blocked for '{query}' (anti-bot protection). Use Apify instead.")
            elif 'GLASSDOOR' in error_msg or 'GOOGLE' in error_msg:
                print(f"⚠️  JobSpy site not supported: {error_msg}")
            else:
                print(f"✗ JobSpy error for '{query}': {e}")
            return []
    
    def _df_row_to_job(self, row: pd.Series) -> Job:
        """Convert DataFrame row to Job model"""
        try:
            # Generate unique ID
            job_id = hashlib.md5(
                f"{row.get('job_url', '')}{row.get('title', '')}".encode()
            ).hexdigest()[:16]
            
            # Parse job type
            job_type = None
            if pd.notna(row.get('job_type')):
                job_type_str = str(row['job_type']).lower()
                if 'full' in job_type_str:
                    job_type = JobType.FULL_TIME
                elif 'part' in job_type_str:
                    job_type = JobType.PART_TIME
                elif 'contract' in job_type_str:
                    job_type = JobType.CONTRACT
            
            # Parse salary
            salary_min = row.get('min_amount') if pd.notna(row.get('min_amount')) else None
            salary_max = row.get('max_amount') if pd.notna(row.get('max_amount')) else None
            
            # Parse date
            posted_date = None
            if pd.notna(row.get('date_posted')):
                try:
                    posted_date = pd.to_datetime(row['date_posted'])
                except:
                    pass
            
            return Job(
                job_id=job_id,
                source=f"jobspy_{row.get('site', 'unknown')}",
                title=row.get('title', 'Unknown'),
                company=row.get('company', 'Unknown'),
                location=row.get('location'),
                is_remote=bool(row.get('is_remote', False)),
                description=row.get('description', ''),
                job_type=job_type,
                salary_min=salary_min,
                salary_max=salary_max,
                currency=row.get('currency'),
                job_url=row.get('job_url', 'https://example.com'),
                company_url=row.get('company_url'),
                posted_date=posted_date,
                scraped_at=datetime.now()
            )
        except Exception as e:
            print(f"Error converting job row: {e}")
            return None