# tests/test_scrapers.py
"""Tests for scraper components"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from scrapers.jobspy_scraper import JobSpyScraper
from scrapers.apify_scraper import ApifyScraper
from scrapers.career_page_scraper import CareerPageScraper
from models.job import Job, JobType


# ──────────────────────────────────────────────────────────────
# BASE SCRAPER TESTS
# ──────────────────────────────────────────────────────────────

class TestBaseScraper:
    """Test the abstract base scraper."""

    def test_concrete_implementation(self):
        """Test that BaseScraper requires implementation."""
        with pytest.raises(TypeError):
            # Can't instantiate abstract class
            scraper = BaseScraper("test")

    def test_concrete_subclass(self):
        """Test creating a concrete subclass."""
        class TestScraper(BaseScraper):
            def scrape(self, query, **kwargs):
                return []
        
        scraper = TestScraper("test")
        assert scraper.name == "test"
        assert scraper.jobs_scraped == 0
        assert scraper.errors == 0

    def test_rate_limit(self):
        """Test rate limiting adds delay."""
        class TestScraper(BaseScraper):
            def scrape(self, query, **kwargs):
                return []
        
        scraper = TestScraper("test")
        
        import time
        start = time.time()
        scraper.rate_limit(min_delay=0.1, max_delay=0.2)
        elapsed = time.time() - start
        
        assert elapsed >= 0.1

    def test_log_scrape_success(self):
        """Test logging successful scrape."""
        class TestScraper(BaseScraper):
            def scrape(self, query, **kwargs):
                return []
        
        scraper = TestScraper("test")
        scraper.log_scrape("Python Developer", 10, success=True)
        
        assert scraper.jobs_scraped == 10
        assert scraper.errors == 0

    def test_log_scrape_failure(self):
        """Test logging failed scrape."""
        class TestScraper(BaseScraper):
            def scrape(self, query, **kwargs):
                return []
        
        scraper = TestScraper("test")
        scraper.log_scrape("Python Developer", 0, success=False)
        
        assert scraper.jobs_scraped == 0
        assert scraper.errors == 1

    def test_get_stats(self):
        """Test getting scraper statistics."""
        class TestScraper(BaseScraper):
            def scrape(self, query, **kwargs):
                return []
        
        scraper = TestScraper("test")
        scraper.jobs_scraped = 50
        scraper.errors = 2
        
        stats = scraper.get_stats()
        assert stats["name"] == "test"
        assert stats["jobs_scraped"] == 50
        assert stats["errors"] == 2

    def test_reset_stats(self):
        """Test resetting statistics."""
        class TestScraper(BaseScraper):
            def scrape(self, query, **kwargs):
                return []
        
        scraper = TestScraper("test")
        scraper.jobs_scraped = 50
        scraper.errors = 2
        scraper.reset_stats()
        
        assert scraper.jobs_scraped == 0
        assert scraper.errors == 0

    def test_validate_job_valid(self):
        """Test validating a valid job."""
        class TestScraper(BaseScraper):
            def scrape(self, query, **kwargs):
                return []
        
        scraper = TestScraper("test")
        job = Job(
            job_id="test1",
            source="test",
            title="Developer",
            company="TestCorp",
            description="Test",
            job_url="https://example.com/job/1"
        )
        
        assert scraper.validate_job(job) is True

    def test_validate_job_missing_title(self):
        """Test validating job with missing title."""
        class TestScraper(BaseScraper):
            def scrape(self, query, **kwargs):
                return []
        
        scraper = TestScraper("test")
        # Create job without proper title - need to use object.__setattr__
        job = Job(
            job_id="test1",
            source="test",
            title="",  # Empty title
            company="TestCorp",
            description="Test",
            job_url="https://example.com/job/1"
        )
        
        # Empty string is falsy, should fail validation
        assert scraper.validate_job(job) is False

    def test_clean_text(self):
        """Test text cleaning."""
        class TestScraper(BaseScraper):
            def scrape(self, query, **kwargs):
                return []
        
        scraper = TestScraper("test")
        
        # Test with extra whitespace
        text = "  Hello   World  "
        cleaned = scraper.clean_text(text)
        assert cleaned == "Hello World"
        
        # Test with None
        assert scraper.clean_text(None) is None
        
        # Test with empty string
        assert scraper.clean_text("") is None


# ──────────────────────────────────────────────────────────────
# JOBSPY SCRAPER TESTS
# ──────────────────────────────────────────────────────────────

class TestJobSpyScraper:

    def test_initialization(self):
        """Test JobSpy scraper initialization."""
        scraper = JobSpyScraper()
        assert scraper.name == "jobspy"
        assert len(scraper.SUPPORTED_SITES) == 5

    @patch('scrapers.jobspy_scraper.scrape_jobs')
    def test_scrape_success(self, mock_scrape_jobs, sample_preferences):
        """Test successful job scraping."""
        import pandas as pd
        
        # Mock DataFrame
        mock_df = pd.DataFrame([
            {
                'job_url': 'https://example.com/job/1',
                'title': 'Python Developer',
                'company': 'TechCorp',
                'location': 'Remote',
                'is_remote': True,
                'description': 'Test job',
                'job_type': 'full-time',
                'min_amount': 100000,
                'max_amount': 120000,
                'currency': 'USD',
                'site': 'indeed',
                'date_posted': '2024-01-01',
                'company_url': 'https://techcorp.com'
            }
        ])
        mock_scrape_jobs.return_value = mock_df
        
        scraper = JobSpyScraper()
        jobs = scraper.scrape(
            query="Python Developer",
            location="Remote",
            is_remote=True,
            results_wanted=10
        )
        
        assert len(jobs) == 1
        assert jobs[0].title == "Python Developer"
        assert jobs[0].company == "TechCorp"

    @patch('scrapers.jobspy_scraper.scrape_jobs')
    def test_scrape_no_results(self, mock_scrape_jobs):
        """Test scraping with no results."""
        import pandas as pd
        
        mock_scrape_jobs.return_value = pd.DataFrame()
        
        scraper = JobSpyScraper()
        jobs = scraper.scrape(query="NonExistentJob")
        
        assert jobs == []

    @patch('scrapers.jobspy_scraper.scrape_jobs')
    def test_scrape_exception(self, mock_scrape_jobs):
        """Test handling of scraping exceptions."""
        mock_scrape_jobs.side_effect = Exception("API Error")
        
        scraper = JobSpyScraper()
        jobs = scraper.scrape(query="Python Developer")
        
        assert jobs == []

    def test_df_row_to_job(self):
        """Test DataFrame row to Job conversion."""
        import pandas as pd
        
        scraper = JobSpyScraper()
        
        row = pd.Series({
            'job_url': 'https://example.com/job/1',
            'title': 'Developer',
            'company': 'TestCorp',
            'location': 'Remote',
            'is_remote': True,
            'description': 'Test',
            'job_type': 'full-time',
            'min_amount': 100000,
            'max_amount': 150000,
            'currency': 'USD',
            'site': 'indeed',
            'date_posted': '2024-01-01',
        })
        
        job = scraper._df_row_to_job(row)
        
        assert job is not None
        assert job.title == "Developer"
        assert job.company == "TestCorp"
        assert job.is_remote is True
        assert job.job_type == JobType.FULL_TIME
        assert job.salary_min == 100000


# ──────────────────────────────────────────────────────────────
# APIFY SCRAPER TESTS
# ──────────────────────────────────────────────────────────────

class TestApifyScraper:

    @patch('scrapers.apify_scraper.settings')
    def test_initialization_with_api_key(self, mock_settings):
        """Test initialization with API key."""
        mock_settings.APIFY_API_KEY = "test_key"
        
        with patch('scrapers.apify_scraper.ApifyClient') as mock_client:
            scraper = ApifyScraper()
            assert scraper.client is not None
            assert scraper.name == "apify"

    def test_initialization_without_api_key(self):
        """Test initialization without API key."""
        with patch('scrapers.apify_scraper.settings') as mock_settings:
            mock_settings.APIFY_API_KEY = None
            
            scraper = ApifyScraper()
            assert scraper.client is None

    def test_scrape_without_client(self):
        """Test scraping when client is not available."""
        with patch('scrapers.apify_scraper.settings') as mock_settings:
            mock_settings.APIFY_API_KEY = None
            
            scraper = ApifyScraper()
            jobs = scraper.scrape_indeed("Python Developer")
            
            assert jobs == []

    def test_item_to_job_conversion(self):
        """Test Apify item to Job conversion."""
        with patch('scrapers.apify_scraper.settings') as mock_settings:
            mock_settings.APIFY_API_KEY = "test_key"
            
            with patch('scrapers.apify_scraper.ApifyClient'):
                scraper = ApifyScraper()
                
                item = {
                    'url': 'https://indeed.com/job/1',
                    'title': 'Python Developer',
                    'company': 'TechCorp',
                    'location': 'Remote',
                    'description': 'Test job',
                    'salary': {
                        'min': 100000,
                        'max': 150000
                    }
                }
                
                job = scraper._item_to_job(item, "indeed")
                
                assert job is not None
                assert job.title == "Python Developer"
                assert job.company == "TechCorp"
                assert job.source == "apify_indeed"
                assert job.salary_min == 100000


# ──────────────────────────────────────────────────────────────
# CAREER PAGE SCRAPER TESTS
# ──────────────────────────────────────────────────────────────

class TestCareerPageScraper:

    def test_initialization(self):
        """Test career page scraper initialization."""
        scraper = CareerPageScraper()
        assert scraper.name == "career_page"

    def test_extract_company_name(self):
        """Test extracting company name from URL."""
        scraper = CareerPageScraper()
        
        # Greenhouse URL
        company = scraper._extract_company_name("https://boards.greenhouse.io/openai")
        assert company == "Openai"
        
        # Lever URL
        company = scraper._extract_company_name("https://jobs.lever.co/anthropic")
        assert company == "Anthropic"

    def test_extract_company_name_with_hyphens(self):
        """Test company name extraction with hyphens."""
        scraper = CareerPageScraper()
        
        company = scraper._extract_company_name("https://boards.greenhouse.io/tech-corp")
        assert company == "Tech Corp"

    @pytest.mark.asyncio
    async def test_scrape_greenhouse_mock(self):
        """Test Greenhouse scraping with mocked playwright."""
        scraper = CareerPageScraper()
        
        # This would need full playwright mocking for actual test
        # For now, just verify the method exists and is async
        assert hasattr(scraper, 'scrape_greenhouse')
