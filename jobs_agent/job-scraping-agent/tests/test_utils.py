# tests/test_utils.py
"""Tests for utility components: deduplicator, database"""

import pytest
import os
import tempfile
from datetime import datetime

from utils.deduplicator import JobDeduplicator
from models.job import Job, JobType


# ──────────────────────────────────────────────────────────────
# DEDUPLICATOR TESTS
# ──────────────────────────────────────────────────────────────

class TestJobDeduplicator:

    def test_deduplicate_empty_list(self):
        """Test deduplicating empty list."""
        deduplicator = JobDeduplicator()
        result = deduplicator.deduplicate([])
        assert result == []

    def test_deduplicate_no_duplicates(self, sample_jobs):
        """Test when there are no duplicates."""
        deduplicator = JobDeduplicator()
        result = deduplicator.deduplicate(sample_jobs)
        
        assert len(result) == 3
        assert result == sample_jobs

    def test_deduplicate_by_url(self):
        """Test deduplication by exact URL match."""
        deduplicator = JobDeduplicator()
        
        jobs = [
            Job(
                job_id="job1",
                source="jobspy",
                title="Python Developer",
                company="Company A",
                description="Test",
                job_url="https://example.com/job/1"
            ),
            Job(
                job_id="job2",
                source="apify",
                title="Python Developer",
                company="Company A",
                description="Duplicate",
                job_url="https://example.com/job/1"  # Same URL
            ),
        ]
        
        result = deduplicator.deduplicate(jobs)
        assert len(result) == 1
        assert result[0].job_id == "job1"

    def test_deduplicate_by_similarity(self):
        """Test deduplication by title+company similarity."""
        deduplicator = JobDeduplicator()
        
        jobs = [
            Job(
                job_id="job1",
                source="jobspy",
                title="Senior Python Developer",
                company="TechCorp",
                description="Test",
                job_url="https://example.com/job/1"
            ),
            Job(
                job_id="job2",
                source="apify",
                title="Senior Python Developer",
                company="TechCorp",
                description="Similar job",
                job_url="https://example.com/job/2"  # Different URL
            ),
        ]
        
        result = deduplicator.deduplicate(jobs)
        # Should be deduplicated due to high similarity
        assert len(result) == 1

    def test_deduplicate_different_companies(self):
        """Test that different companies are not deduplicated."""
        deduplicator = JobDeduplicator()
        
        jobs = [
            Job(
                job_id="job1",
                source="jobspy",
                title="Senior Python Developer",
                company="Microsoft",
                description="Test",
                job_url="https://example.com/job/1"
            ),
            Job(
                job_id="job2",
                source="apify",
                title="Python Developer Intern",
                company="Google",
                description="Different company",
                job_url="https://example.com/job/2"
            ),
        ]
        
        result = deduplicator.deduplicate(jobs)
        # Different companies and different titles should not be deduplicated
        assert len(result) == 2

    def test_deduplicate_different_titles(self):
        """Test that different titles are not deduplicated."""
        deduplicator = JobDeduplicator()
        
        jobs = [
            Job(
                job_id="job1",
                source="jobspy",
                title="Python Developer",
                company="TechCorp",
                description="Python role",
                job_url="https://example.com/job/1"
            ),
            Job(
                job_id="job2",
                source="apify",
                title="Java Developer",
                company="TechCorp",
                description="Java role",
                job_url="https://example.com/job/2"
            ),
        ]
        
        result = deduplicator.deduplicate(jobs)
        assert len(result) == 2

    def test_create_signature(self):
        """Test signature creation for matching."""
        deduplicator = JobDeduplicator()
        
        job = Job(
            job_id="test1",
            source="test",
            title="Python Developer",
            company="TechCorp",
            description="Test",
            job_url="https://example.com/job/1"
        )
        
        signature = deduplicator._create_signature(job)
        assert signature == "techcorp::python developer"

    def test_is_duplicate_signature_exact_match(self):
        """Test exact signature match."""
        deduplicator = JobDeduplicator()
        
        seen = {"techcorp::python developer", "google::software engineer"}
        is_dup = deduplicator._is_duplicate_signature(
            "techcorp::python developer",
            seen
        )
        
        assert is_dup is True

    def test_is_duplicate_signature_similar(self):
        """Test similar signature match."""
        deduplicator = JobDeduplicator()
        
        seen = {"techcorp::senior python developer"}
        is_dup = deduplicator._is_duplicate_signature(
            "techcorp::python developer",
            seen,
            threshold=0.85
        )
        
        # Should be considered duplicate due to high similarity
        assert is_dup is True

    def test_is_duplicate_signature_different(self):
        """Test different signatures."""
        deduplicator = JobDeduplicator()
        
        seen = {"google::software engineer"}
        is_dup = deduplicator._is_duplicate_signature(
            "techcorp::python developer",
            seen
        )
        
        assert is_dup is False

    def test_deduplicate_preserves_first_occurrence(self):
        """Test that first occurrence is preserved."""
        deduplicator = JobDeduplicator()
        
        jobs = [
            Job(
                job_id="original",
                source="jobspy",
                title="Python Developer",
                company="TechCorp",
                description="Original job",
                job_url="https://example.com/job/1"
            ),
            Job(
                job_id="duplicate",
                source="apify",
                title="Python Developer",
                company="TechCorp",
                description="Duplicate job",
                job_url="https://example.com/job/2"
            ),
        ]
        
        result = deduplicator.deduplicate(jobs)
        assert len(result) == 1
        assert result[0].job_id == "original"


# ──────────────────────────────────────────────────────────────
# DATABASE TESTS
# ──────────────────────────────────────────────────────────────

class TestDatabase:

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        from utils.database import Database
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_jobs.db")
            
            # Mock settings to use temp database
            import unittest.mock as mock
            with mock.patch('utils.database.settings') as mock_settings:
                mock_settings.DATABASE_URL = f"sqlite:///{db_path}"
                db = Database()
                yield db

    def test_save_single_job(self, temp_db, sample_job):
        """Test saving a single job."""
        temp_db.save_jobs([sample_job])
        
        # Verify job was saved
        from utils.database import JobDB
        saved_job = temp_db.session.query(JobDB).filter_by(job_id="test123").first()
        
        assert saved_job is not None
        assert saved_job.title == "Senior Python Developer"
        assert saved_job.company == "TechCorp"

    def test_save_multiple_jobs(self, temp_db, sample_jobs):
        """Test saving multiple jobs."""
        temp_db.save_jobs(sample_jobs)
        
        from utils.database import JobDB
        count = temp_db.session.query(JobDB).count()
        
        assert count == 3

    def test_save_duplicate_jobs(self, temp_db, sample_job):
        """Test that duplicate jobs are skipped."""
        # Save job twice
        temp_db.save_jobs([sample_job])
        temp_db.save_jobs([sample_job])
        
        from utils.database import JobDB
        count = temp_db.session.query(JobDB).count()
        
        # Should only have one job
        assert count == 1

    def test_save_job_with_all_fields(self, temp_db):
        """Test saving job with all fields populated."""
        job = Job(
            job_id="complete1",
            source="jobspy",
            title="Full Stack Developer",
            company="TechCorp",
            location="Remote",
            is_remote=True,
            description="Full stack role",
            job_type=JobType.FULL_TIME,
            salary_min=120000,
            salary_max=160000,
            currency="USD",
            job_url="https://example.com/job/1",
            posted_date=datetime.now(),
            match_score=85.5
        )
        
        temp_db.save_jobs([job])
        
        from utils.database import JobDB
        saved = temp_db.session.query(JobDB).filter_by(job_id="complete1").first()
        
        assert saved.title == "Full Stack Developer"
        assert saved.is_remote is True
        assert saved.salary_min == 120000
        assert saved.match_score == 85.5

    def test_database_initialization(self, temp_db):
        """Test database is properly initialized."""
        from utils.database import JobDB
        
        # Should be able to query without errors
        count = temp_db.session.query(JobDB).count()
        assert count == 0  # Empty initially
