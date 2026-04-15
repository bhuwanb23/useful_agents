# phase2-matching/tests/test_scorers.py
import pytest
from scorers.traditional_scorer import TraditionalScorer
from scorers.hybrid_scorer import HybridScorer
from models.scored_job import ScoreBreakdown, MatchGrade

class TestTraditionalScorer:
    """Test traditional (rule-based) scoring."""
    
    def test_high_match_job(self, sample_resume_analysis, sample_preferences, sample_job):
        """Test scoring a high-match job."""
        scorer = TraditionalScorer(sample_resume_analysis, sample_preferences)
        
        breakdown = scorer.score(sample_job)
        
        assert breakdown.skills_match > 15.0  # Should be good skill match
        assert breakdown.experience_match > 5.0
        assert breakdown.title_match > 8.0
        assert breakdown.salary_match > 5.0
        assert breakdown.location_match == 5.0  # Remote job, remote preferred
    
    def test_low_match_job(self, sample_resume_analysis, sample_preferences):
        """Test scoring a low-match job."""
        scorer = TraditionalScorer(sample_resume_analysis, sample_preferences)
        
        low_match_job = {
            "job_id": "test_low_001",
            "title": "Junior Graphic Designer",
            "company": "DesignStudio",
            "location": "London, UK",
            "is_remote": False,
            "description": "Looking for graphic designer with Photoshop and Illustrator skills",
            "job_url": "https://example.com/low",
            "salary_min": 40000,
            "salary_max": 50000,
            "posted_date": "2024-01-15",
            "source": "apify"
        }
        
        breakdown = scorer.score(low_match_job)
        
        # Skills should be low (no tech skills match)
        assert breakdown.skills_match < 15.0
        # Location should be low (not remote, not in preferred locations)
        assert breakdown.location_match < 3.0
        # Salary should be low (below minimum)
        assert breakdown.salary_match < 5.0
    
    def test_score_breakdown_structure(self, sample_resume_analysis, sample_preferences, sample_job):
        """Test that score breakdown has correct structure."""
        scorer = TraditionalScorer(sample_resume_analysis, sample_preferences)
        
        breakdown = scorer.score(sample_job)
        
        assert isinstance(breakdown, ScoreBreakdown)
        assert breakdown.skills_match >= 0
        assert breakdown.experience_match >= 0
        assert breakdown.title_match >= 0
        assert breakdown.semantic_similarity == 0  # Not set by traditional scorer
        assert breakdown.salary_match >= 0
        assert breakdown.location_match >= 0
        assert breakdown.culture_fit == 0  # Not set by traditional scorer
        assert breakdown.growth_potential == 0  # Not set by traditional scorer
    
    def test_calculate_total_score(self, sample_resume_analysis, sample_preferences, sample_job):
        """Test total score calculation."""
        scorer = TraditionalScorer(sample_resume_analysis, sample_preferences)
        
        breakdown = scorer.score(sample_job)
        total = scorer.calculate_total(breakdown)
        
        assert total > 0
        assert total <= 100.0
    
    def test_score_with_missing_fields(self, sample_resume_analysis, sample_preferences):
        """Test scoring job with missing fields."""
        scorer = TraditionalScorer(sample_resume_analysis, sample_preferences)
        
        incomplete_job = {
            "job_id": "test_incomplete",
            "title": "Developer",
            "company": "Company",
            "location": None,
            "is_remote": False,
            "description": "Developer position",
            "job_url": "https://example.com",
            # No salary info
        }
        
        # Should not raise exception
        breakdown = scorer.score(incomplete_job)
        
        assert breakdown.skills_match >= 0
        assert breakdown.salary_match >= 0


class TestHybridScorer:
    """Test hybrid scoring (traditional + AI)."""
    
    def test_hybrid_without_ai(self, sample_resume_analysis, sample_preferences, sample_job):
        """Test hybrid scorer with AI disabled."""
        scorer = HybridScorer(
            resume_analysis=sample_resume_analysis,
            preferences=sample_preferences,
            api_key=None,
            use_ai=False
        )
        
        breakdown = scorer.score(sample_job, resume_text="Python Developer")
        
        # Should have neutral AI scores
        assert breakdown.semantic_similarity == 7.5  # Neutral
        assert breakdown.culture_fit == 2.5  # Neutral
        assert breakdown.growth_potential == 2.5  # Neutral
        
        # Traditional scores should be present
        assert breakdown.skills_match > 0
        assert breakdown.title_match > 0
    
    def test_hybrid_score_with_explanation(self, sample_resume_analysis, sample_preferences, sample_job):
        """Test scoring with explanation (AI disabled)."""
        scorer = HybridScorer(
            resume_analysis=sample_resume_analysis,
            preferences=sample_preferences,
            api_key=None,
            use_ai=False
        )
        
        breakdown, explanation, missing_skills = scorer.score_with_explanation(
            job=sample_job,
            resume_text="Python Developer"
        )
        
        assert breakdown is not None
        assert isinstance(breakdown, ScoreBreakdown)
        # Explanation may be empty when AI disabled
        assert missing_skills is not None
    
    def test_calculate_total_from_breakdown(self, sample_resume_analysis, sample_preferences, sample_job):
        """Test calculating total score."""
        scorer = HybridScorer(
            resume_analysis=sample_resume_analysis,
            preferences=sample_preferences,
            api_key=None,
            use_ai=False
        )
        
        breakdown = scorer.score(sample_job, "Python Developer")
        total = scorer.calculate_total(breakdown)
        
        assert total > 0
        assert total <= 100.0
