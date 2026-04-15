# phase2-matching/tests/conftest.py
import pytest
import sys
import os
from pathlib import Path
import json
import tempfile
import sqlite3
from datetime import datetime

# CRITICAL: Add phase2-matching to path BEFORE any other imports
CURRENT_DIR = Path(__file__).parent
PHASE2_DIR = CURRENT_DIR.parent

# Remove any existing phase2-matching paths to avoid duplicates
sys.path = [p for p in sys.path if 'phase2-matching' not in p]

# Add at the very beginning
sys.path.insert(0, str(PHASE2_DIR))

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = str(PHASE2_DIR)

@pytest.fixture
def sample_resume_analysis():
    """Create sample resume analysis data."""
    return {
        "name": "John Doe",
        "email": "john.doe@email.com",
        "skills": [
            "Python", "JavaScript", "TypeScript", "SQL", "FastAPI", "Django",
            "React", "PostgreSQL", "MongoDB", "Redis", "AWS", "Docker",
            "Kubernetes", "Git", "REST APIs", "GraphQL"
        ],
        "job_titles": ["Senior Backend Engineer", "Software Engineer", "Python Developer"],
        "experience_years": 5,
        "seniority": "senior",
        "industries": ["Technology", "Software"],
        "education": "Bachelor of Science in Computer Science",
        "certifications": ["AWS Certified Solutions Architect", "CKAD"],
        "search_queries": ["Python Developer", "Backend Engineer", "Software Engineer"],
        "alternative_titles": ["Full Stack Developer", "Backend Developer"],
        "priority_skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"]
    }

@pytest.fixture
def sample_preferences():
    """Create sample job preferences."""
    return {
        "remote_only": True,
        "locations": ["United States", "Remote"],
        "min_salary": 100000,
        "max_salary": 180000,
        "job_types": ["full-time"],
        "preferred_industries": ["Technology", "SaaS"],
        "excluded_companies": [],
        "excluded_keywords": ["intern", "junior", "volunteer"]
    }

@pytest.fixture
def sample_job():
    """Create a sample job dictionary."""
    return {
        "job_id": "test_job_001",
        "title": "Senior Python Developer",
        "company": "TechCorp Inc.",
        "location": "Remote",
        "is_remote": True,
        "description": """
        We are looking for a Senior Python Developer with experience in:
        - Python, FastAPI, Django
        - PostgreSQL, Redis
        - AWS, Docker, Kubernetes
        - REST APIs and microservices
        - Git and CI/CD
        Requirements:
        - 5+ years Python experience
        - Experience with cloud platforms
        - Strong problem-solving skills
        """,
        "job_url": "https://example.com/job/001",
        "salary_min": 120000,
        "salary_max": 160000,
        "posted_date": "2024-01-15",
        "source": "apify_indeed"
    }

@pytest.fixture
def sample_jobs():
    """Create a list of sample jobs."""
    return [
        {
            "job_id": "job_001",
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "location": "Remote",
            "is_remote": True,
            "description": "Looking for Python, FastAPI, PostgreSQL, AWS expert with 5+ years experience",
            "job_url": "https://example.com/job/001",
            "salary_min": 130000,
            "salary_max": 170000,
            "posted_date": "2024-01-15",
            "source": "apify"
        },
        {
            "job_id": "job_002",
            "title": "Backend Engineer",
            "company": "StartupXYZ",
            "location": "San Francisco, CA",
            "is_remote": False,
            "description": "Backend engineer needed: Python, Django, Redis, Docker, Kubernetes",
            "job_url": "https://example.com/job/002",
            "salary_min": 110000,
            "salary_max": 150000,
            "posted_date": "2024-01-14",
            "source": "apify"
        },
        {
            "job_id": "job_003",
            "title": "Full Stack Developer",
            "company": "WebSolutions",
            "location": "Remote",
            "is_remote": True,
            "description": "Full stack role: React, Python, JavaScript, PostgreSQL, Git",
            "job_url": "https://example.com/job/003",
            "salary_min": 95000,
            "salary_max": 130000,
            "posted_date": "2024-01-13",
            "source": "apify"
        }
    ]

@pytest.fixture
def temp_jobs_db(sample_jobs):
    """Create a temporary SQLite database with sample jobs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_jobs.db")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create jobs table
        cursor.execute("""
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                is_remote BOOLEAN,
                description TEXT,
                job_url TEXT,
                salary_min REAL,
                salary_max REAL,
                posted_date TEXT,
                source TEXT
            )
        """)
        
        # Insert sample jobs
        for job in sample_jobs:
            cursor.execute("""
                INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job['job_id'],
                job['title'],
                job['company'],
                job['location'],
                job['is_remote'],
                job['description'],
                job['job_url'],
                job['salary_min'],
                job['salary_max'],
                job['posted_date'],
                job['source']
            ))
        
        conn.commit()
        conn.close()
        
        yield db_path

@pytest.fixture
def temp_resume_file(sample_resume_analysis):
    """Create a temporary resume analysis JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_resume_analysis, f, indent=2)
        f.flush()  # Ensure data is written
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_preferences_file(sample_preferences):
    """Create a temporary preferences JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_preferences, f, indent=2)
        f.flush()  # Ensure data is written
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def sample_skill_text():
    """Sample text with skills for testing skill extraction."""
    return """
    We need someone proficient in Python and JavaScript.
    Experience with React, Django, and PostgreSQL required.
    Knowledge of AWS, Docker, and Kubernetes is a plus.
    Familiarity with CI/CD, Git, and Agile methodologies.
    """

@pytest.fixture
def sample_embedding_cache():
    """Create a mock embedding cache."""
    class MockEmbeddingCache:
        def __init__(self):
            self.cache = {}
        
        def get(self, key):
            return self.cache.get(key)
        
        def set(self, key, value):
            self.cache[key] = value
        
        def save(self):
            pass
        
        def load(self):
            pass
    
    return MockEmbeddingCache()
