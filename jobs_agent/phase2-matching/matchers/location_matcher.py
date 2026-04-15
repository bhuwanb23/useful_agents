# phase2-matching/matchers/location_matcher.py
from typing import List, Optional

class LocationMatcher:
    """
    Match location preferences
    """
    
    def calculate_match(
        self,
        preferred_locations: List[str],
        remote_only: bool,
        job_location: Optional[str],
        job_is_remote: bool,
        max_score: float = 5.0
    ) -> float:
        """
        Calculate location match score (max 5 points)
        """
        # Remote preference
        if remote_only:
            return max_score if job_is_remote else 0.0
        
        # Remote is always acceptable
        if job_is_remote:
            return max_score
        
        # No preference = full score
        if not preferred_locations:
            return max_score
        
        # Check location match
        if not job_location:
            return max_score * 0.5  # Unknown location = neutral
        
        job_location_lower = job_location.lower()
        
        for preferred in preferred_locations:
            if preferred.lower() in job_location_lower:
                return max_score
        
        return 0.0  # Location doesn't match