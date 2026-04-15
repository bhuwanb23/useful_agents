# utils/deduplicator.py
from typing import List
from models.job import Job
from difflib import SequenceMatcher

class JobDeduplicator:
    """
    Remove duplicate jobs using multiple strategies
    """
    
    def deduplicate(self, jobs: List[Job]) -> List[Job]:
        """
        Deduplicate jobs based on:
        1. Exact URL match
        2. Similar title + company
        """
        seen_urls = set()
        seen_signatures = set()
        unique_jobs = []
        
        for job in jobs:
            # Strategy 1: URL dedup
            if job.job_url in seen_urls:
                continue
            
            # Strategy 2: Title + Company similarity
            signature = self._create_signature(job)
            if self._is_duplicate_signature(signature, seen_signatures):
                continue
            
            seen_urls.add(job.job_url)
            seen_signatures.add(signature)
            unique_jobs.append(job)
        
        return unique_jobs
    
    def _create_signature(self, job: Job) -> str:
        """Create a signature for fuzzy matching"""
        title = job.title.lower().strip()
        company = job.company.lower().strip()
        return f"{company}::{title}"
    
    def _is_duplicate_signature(
        self,
        signature: str,
        seen: set,
        threshold: float = 0.85
    ) -> bool:
        """Check if signature is similar to any seen signatures"""
        for seen_sig in seen:
            similarity = SequenceMatcher(None, signature, seen_sig).ratio()
            if similarity >= threshold:
                return True
        return False