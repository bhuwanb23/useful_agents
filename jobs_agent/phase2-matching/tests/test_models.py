# phase2-matching/tests/test_models.py
import pytest
from models.scored_jobs import ScoredJob, ScoreBreakdown, MatchExplanation, MatchGrade
from datetime import datetime

class TestScoreBreakdown:
    """Test ScoreBreakdown model."""
    
    def test_default_values(self):
        """Test default values."""
        breakdown = ScoreBreakdown()
        
        assert breakdown.skills_match == 0.0
        assert breakdown.experience_match == 0.0
        assert breakdown.title_match == 0.0
        assert breakdown.semantic_similarity == 0.0
        assert breakdown.salary_match == 0.0
        assert breakdown.location_match == 0.0
        assert breakdown.culture_fit == 0.0
        assert breakdown.growth_potential == 0.0
    
    def test_custom_values(self):
        """Test custom values."""
        breakdown = ScoreBreakdown(
            skills_match=25.0,
            experience_match=12.0,
            title_match=13.0,
            semantic_similarity=10.0,
            salary_match=8.0,
            location_match=5.0,
            culture_fit=4.0,
            growth_potential=4.0
        )
        
        assert breakdown.skills_match == 25.0
        assert breakdown.experience_match == 12.0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        breakdown = ScoreBreakdown(
            skills_match=25.0,
            experience_match=12.0,
            title_match=13.0
        )
        
        result = breakdown.to_dict()
        
        assert isinstance(result, dict)
        assert result['skills'] == 25.0
        assert result['experience'] == 12.0
        assert result['title'] == 13.0


class TestMatchExplanation:
    """Test MatchExplanation model."""
    
    def test_default_values(self):
        """Test default values."""
        explanation = MatchExplanation()
        
        assert explanation.strengths == []
        assert explanation.concerns == []
        assert explanation.missing_skills == []
        assert explanation.ai_summary is None
        assert explanation.recommendation == ""
    
    def test_with_values(self):
        """Test with custom values."""
        explanation = MatchExplanation(
            strengths=["Great skill match", "Perfect location"],
            concerns=["Salary below expectations"],
            missing_skills=["Kubernetes", "Terraform"],
            ai_summary="Excellent candidate",
            recommendation="HIGHLY RECOMMENDED"
        )
        
        assert len(explanation.strengths) == 2
        assert len(explanation.concerns) == 1
        assert explanation.recommendation == "HIGHLY RECOMMENDED"


class TestScoredJob:
    """Test ScoredJob model."""
    
    @pytest.fixture
    def sample_scored_job(self):
        """Create a sample ScoredJob."""
        return ScoredJob(
            job_id="test_001",
            title="Senior Python Developer",
            company="TechCorp",
            location="Remote",
            is_remote=True,
            job_url="https://example.com/job",
            description="Python developer position",
            salary_min=120000,
            salary_max=160000,
            posted_date=datetime.now(),
            source="apify",
            total_score=85.5,
            grade="A+",
            breakdown=ScoreBreakdown(
                skills_match=25.0,
                experience_match=12.0,
                title_match=13.0,
                semantic_similarity=10.0,
                salary_match=8.0,
                location_match=5.0,
                culture_fit=4.0,
                growth_potential=4.0
            ),
            explanation=MatchExplanation(
                strengths=["Excellent skills", "Great location"],
                concerns=[],
                missing_skills=["Kubernetes"],
                recommendation="HIGHLY RECOMMENDED"
            )
        )
    
    def test_scored_job_creation(self, sample_scored_job):
        """Test creating a ScoredJob."""
        assert sample_scored_job.job_id == "test_001"
        assert sample_scored_job.title == "Senior Python Developer"
        assert sample_scored_job.total_score == 85.5
        assert sample_scored_job.grade == "A+"
    
    def test_score_percentage(self, sample_scored_job):
        """Test score_percentage property."""
        assert sample_scored_job.score_percentage == 85
    
    def test_is_recommended(self, sample_scored_job):
        """Test is_recommended property."""
        assert sample_scored_job.is_recommended is True  # Score >= 65
    
    def test_not_recommended_job(self):
        """Test job that is not recommended."""
        job = ScoredJob(
            job_id="test_002",
            title="Junior Designer",
            company="DesignStudio",
            location="London",
            is_remote=False,
            job_url="https://example.com/job2",
            description="Design position",
            salary_min=40000,
            salary_max=50000,
            posted_date=datetime.now(),
            source="apify",
            total_score=35.0,
            grade="F",
            breakdown=ScoreBreakdown(),
            explanation=MatchExplanation()
        )
        
        assert job.is_recommended is False  # Score < 65
    
    def test_model_dump(self, sample_scored_job):
        """Test model serialization."""
        data = sample_scored_job.model_dump(mode='json')
        
        assert isinstance(data, dict)
        assert 'job_id' in data
        assert 'total_score' in data
        assert 'breakdown' in data
        assert 'explanation' in data
    
    def test_remote_job(self, sample_scored_job):
        """Test remote job flag."""
        assert sample_scored_job.is_remote is True
        assert sample_scored_job.location == "Remote"
    
    def test_optional_fields(self):
        """Test optional fields."""
        job = ScoredJob(
            job_id="test_003",
            title="Developer",
            company="Company",
            location=None,
            is_remote=False,
            job_url="https://example.com",
            description="Job",
            salary_min=None,
            salary_max=None,
            posted_date=None,
            source="apify",
            total_score=70.0,
            grade="B",
            breakdown=ScoreBreakdown(),
            explanation=MatchExplanation()
        )
        
        assert job.location is None
        assert job.salary_min is None
        assert job.salary_max is None
    
    def test_grade_enum_values(self):
        """Test all grade enum values."""
        grades = ["A+", "A", "B", "C", "D", "F"]
        
        for grade in grades:
            job = ScoredJob(
                job_id=f"test_{grade}",
                title="Developer",
                company="Company",
                location="Remote",
                is_remote=True,
                job_url="https://example.com",
                description="Job",
                salary_min=100000,
                salary_max=130000,
                posted_date=datetime.now(),
                source="apify",
                total_score=50.0,
                grade=grade,
                breakdown=ScoreBreakdown(),
                explanation=MatchExplanation()
            )
            
            assert job.grade == grade


class TestMatchGrade:
    """Test MatchGrade enum."""
    
    def test_all_grades_exist(self):
        """Test all grade values exist."""
        assert MatchGrade.A_PLUS.value == "A+"
        assert MatchGrade.A.value == "A"
        assert MatchGrade.B.value == "B"
        assert MatchGrade.C.value == "C"
        assert MatchGrade.D.value == "D"
        assert MatchGrade.F.value == "F"
    
    def test_grade_comparison(self):
        """Test grade values can be compared."""
        # Just ensure they're accessible
        assert MatchGrade.A_PLUS.value in ["A+", "A", "B", "C", "D", "F"]
