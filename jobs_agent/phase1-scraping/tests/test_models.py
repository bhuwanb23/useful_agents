# tests/test_models.py
"""Tests for data models: Job, JobPreferences, ResumeAnalysis"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from models.job import Job, JobType
from models.preferences import JobPreferences
from models.resume import ResumeAnalysis


# ──────────────────────────────────────────────────────────────
# JOB MODEL TESTS
# ──────────────────────────────────────────────────────────────

class TestJobModel:

    def test_create_valid_job(self, sample_job):
        """Test creating a valid job."""
        assert sample_job.job_id == "test123"
        assert sample_job.title == "Senior Python Developer"
        assert sample_job.company == "TechCorp"
        assert sample_job.is_remote is True
        assert sample_job.job_type == JobType.FULL_TIME

    def test_job_with_minimal_fields(self):
        """Test creating job with only required fields."""
        job = Job(
            job_id="minimal1",
            source="test",
            title="Developer",
            company="TestCorp",
            description="Test job",
            job_url="https://example.com/job/1"
        )
        
        assert job.job_id == "minimal1"
        assert job.location is None
        assert job.is_remote is False
        assert job.salary_min is None

    def test_job_type_enum(self):
        """Test job type enum values."""
        assert JobType.FULL_TIME.value == "full-time"
        assert JobType.PART_TIME.value == "part-time"
        assert JobType.CONTRACT.value == "contract"
        assert JobType.INTERNSHIP.value == "internship"

    def test_job_serialization(self, sample_job):
        """Test job model serialization."""
        data = sample_job.model_dump()
        assert data["job_id"] == "test123"
        assert data["title"] == "Senior Python Developer"
        assert data["is_remote"] is True

    def test_job_json_schema(self):
        """Test job model has proper JSON schema."""
        schema = Job.model_json_schema()
        assert "properties" in schema
        assert "job_id" in schema["properties"]
        assert "title" in schema["properties"]

    def test_job_url_validation(self):
        """Test that job URL must be valid."""
        with pytest.raises(ValidationError):
            Job(
                job_id="invalid1",
                source="test",
                title="Developer",
                company="TestCorp",
                description="Test",
                job_url="not-a-url"  # Invalid URL
            )

    def test_job_with_salary_range(self):
        """Test job with salary information."""
        job = Job(
            job_id="salary1",
            source="test",
            title="Developer",
            company="TestCorp",
            description="Test",
            job_url="https://example.com/job/1",
            salary_min=100000,
            salary_max=150000,
            currency="USD"
        )
        
        assert job.salary_min == 100000
        assert job.salary_max == 150000
        assert job.currency == "USD"

    def test_job_required_skills(self):
        """Test job with required skills list."""
        job = Job(
            job_id="skills1",
            source="test",
            title="Python Developer",
            company="TestCorp",
            description="Test",
            job_url="https://example.com/job/1",
            required_skills=["Python", "FastAPI", "PostgreSQL"]
        )
        
        assert len(job.required_skills) == 3
        assert "Python" in job.required_skills


# ──────────────────────────────────────────────────────────────
# JOB PREFERENCES TESTS
# ──────────────────────────────────────────────────────────────

class TestJobPreferences:

    def test_default_preferences(self):
        """Test default preference values."""
        prefs = JobPreferences()
        
        assert prefs.remote_only is False
        assert prefs.countries == ["USA"]
        assert prefs.job_types == ["full-time"]
        assert prefs.results_per_source == 50

    def test_custom_preferences(self, sample_preferences):
        """Test custom preference configuration."""
        assert sample_preferences.remote_only is True
        assert len(sample_preferences.locations) == 1
        assert sample_preferences.min_salary == 80000
        assert len(sample_preferences.excluded_keywords) == 3

    def test_preferences_with_multiple_locations(self):
        """Test preferences with multiple locations."""
        prefs = JobPreferences(
            locations=["New York", "San Francisco", "Seattle"],
            countries=["USA", "Canada"]
        )
        
        assert len(prefs.locations) == 3
        assert len(prefs.countries) == 2

    def test_preferences_salary_range(self):
        """Test preferences with salary range."""
        prefs = JobPreferences(
            min_salary=80000,
            max_salary=150000
        )
        
        assert prefs.min_salary == 80000
        assert prefs.max_salary == 150000

    def test_preferences_exclusions(self):
        """Test preference exclusion lists."""
        prefs = JobPreferences(
            excluded_companies=["BadCorp", "EvilInc"],
            excluded_keywords=["unpaid", "volunteer"]
        )
        
        assert len(prefs.excluded_companies) == 2
        assert len(prefs.excluded_keywords) == 2

    def test_preferences_serialization(self):
        """Test preferences serialization."""
        prefs = JobPreferences(remote_only=True, min_salary=100000)
        data = prefs.model_dump()
        
        assert data["remote_only"] is True
        assert data["min_salary"] == 100000


# ──────────────────────────────────────────────────────────────
# RESUME ANALYSIS TESTS
# ──────────────────────────────────────────────────────────────

class TestResumeAnalysis:

    def test_create_resume_analysis(self, sample_resume_analysis):
        """Test creating resume analysis."""
        assert len(sample_resume_analysis.job_titles) == 3
        assert len(sample_resume_analysis.skills) == 5
        assert sample_resume_analysis.experience_years == 5.0
        assert sample_resume_analysis.seniority == "senior"

    def test_resume_analysis_required_fields(self):
        """Test that all required fields are present."""
        analysis = ResumeAnalysis(
            job_titles=["Developer"],
            skills=["Python"],
            experience_years=1.0,
            seniority="entry",
            industries=["Tech"],
            education="Bachelor's",
            certifications=[],
            search_queries=["Python Developer"],
            alternative_titles=[],
            priority_skills=["Python"]
        )
        
        assert analysis.job_titles == ["Developer"]
        assert analysis.seniority == "entry"

    def test_resume_analysis_with_certifications(self):
        """Test resume analysis with certifications."""
        analysis = ResumeAnalysis(
            job_titles=["Engineer"],
            skills=["AWS"],
            experience_years=3.0,
            seniority="mid",
            industries=["Cloud"],
            education="Bachelor's",
            certifications=["AWS Solutions Architect", "AWS Developer"],
            search_queries=[],
            alternative_titles=[],
            priority_skills=[]
        )
        
        assert len(analysis.certifications) == 2

    def test_resume_analysis_serialization(self, sample_resume_analysis):
        """Test resume analysis serialization."""
        data = sample_resume_analysis.model_dump()
        
        assert "job_titles" in data
        assert "skills" in data
        assert "search_queries" in data

    def test_resume_analysis_json_output(self, sample_resume_analysis):
        """Test JSON output format."""
        json_str = sample_resume_analysis.model_dump_json()
        assert "job_titles" in json_str
        assert "Python" in json_str
