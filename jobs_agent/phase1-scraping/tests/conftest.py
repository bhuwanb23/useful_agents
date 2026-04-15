# tests/conftest.py
# Shared fixtures for all job scraping agent tests

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from datetime import datetime

# Add project root to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from models.job import Job, JobType
from models.preferences import JobPreferences
from models.resume import ResumeAnalysis


@pytest.fixture
def sample_job():
    """Create a sample job for testing."""
    return Job(
        job_id="test123",
        source="jobspy",
        title="Senior Python Developer",
        company="TechCorp",
        location="Remote",
        is_remote=True,
        description="We are looking for a senior Python developer...",
        job_type=JobType.FULL_TIME,
        salary_min=120000,
        salary_max=150000,
        currency="USD",
        job_url="https://example.com/job/123",
        posted_date=datetime.now(),
    )


@pytest.fixture
def sample_jobs():
    """Create multiple sample jobs."""
    return [
        Job(
            job_id="job1",
            source="jobspy",
            title="Python Developer",
            company="Company A",
            location="Remote",
            is_remote=True,
            description="Python developer position",
            job_type=JobType.FULL_TIME,
            salary_min=100000,
            job_url="https://example.com/job/1",
        ),
        Job(
            job_id="job2",
            source="apify",
            title="Senior Python Engineer",
            company="Company B",
            location="San Francisco, CA",
            is_remote=False,
            description="Senior engineer role",
            job_type=JobType.FULL_TIME,
            salary_min=140000,
            salary_max=170000,
            job_url="https://example.com/job/2",
        ),
        Job(
            job_id="job3",
            source="greenhouse",
            title="Backend Developer",
            company="Startup C",
            location="New York, NY",
            is_remote=False,
            description="Backend developer",
            job_url="https://example.com/job/3",
        ),
    ]


@pytest.fixture
def sample_preferences():
    """Create sample job preferences."""
    return JobPreferences(
        remote_only=True,
        locations=["United States"],
        countries=["USA"],
        job_types=["full-time"],
        min_salary=80000,
        results_per_source=30,
        excluded_keywords=["unpaid", "volunteer", "intern"]
    )


@pytest.fixture
def sample_resume_analysis():
    """Create sample resume analysis."""
    return ResumeAnalysis(
        job_titles=["Software Engineer", "Python Developer", "Backend Developer"],
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        experience_years=5.0,
        seniority="senior",
        industries=["SaaS", "Technology"],
        education="Bachelor's in Computer Science",
        certifications=["AWS Certified Developer"],
        search_queries=[
            "Senior Python Developer",
            "Backend Engineer Python",
            "Software Engineer Remote"
        ],
        alternative_titles=["Python Engineer", "Full Stack Developer"],
        priority_skills=["Python", "FastAPI", "PostgreSQL"]
    )


@pytest.fixture
def mock_ai_analyzer():
    """Create a mock AI analyzer."""
    analyzer = MagicMock()
    analyzer.analyze_resume.return_value = ResumeAnalysis(
        job_titles=["Software Engineer"],
        skills=["Python", "JavaScript"],
        experience_years=3.0,
        seniority="mid",
        industries=["Technology"],
        education="Bachelor's",
        certifications=[],
        search_queries=["Python Developer"],
        alternative_titles=["Developer"],
        priority_skills=["Python"]
    )
    analyzer.generate_search_queries.return_value = [
        "Python Developer",
        "Software Engineer"
    ]
    return analyzer


@pytest.fixture
def sample_resume_content():
    """Sample resume markdown content."""
    return """
# John Doe
## Software Engineer

### Experience
**Senior Python Developer** - TechCorp (2020-2024)
- Developed microservices using Python and FastAPI
- Managed PostgreSQL databases
- Deployed applications on AWS

### Skills
- Python, FastAPI, Django
- PostgreSQL, MongoDB
- Docker, Kubernetes
- AWS, GCP

### Education
Bachelor's in Computer Science - MIT (2016-2020)

### Certifications
- AWS Certified Developer
"""
