# phase2-matching/matchers/salary_matcher.py
from typing import Optional

class SalaryMatcher:
    """
    Match salary expectations
    """
    
    def calculate_match(
        self,
        min_expected: Optional[float],
        job_min: Optional[float],
        job_max: Optional[float],
        max_score: float = 10.0
    ) -> float:
        """
        Calculate salary match score (max 10 points)
        """
        if not min_expected or not job_min:
            return max_score * 0.5  # Neutral if no data
        
        if job_min >= min_expected:
            # Job pays what you want or more
            if job_max and job_max >= min_expected * 1.2:
                return max_score  # 20%+ above = excellent
            else:
                return max_score * 0.8  # Acceptable
        else:
            # Job pays less
            gap = (min_expected - job_min) / min_expected
            
            if gap <= 0.10:
                return max_score * 0.6  # Within 10% = negotiable
            elif gap <= 0.20:
                return max_score * 0.3  # Within 20% = maybe
            else:
                return 0.0  # Too low