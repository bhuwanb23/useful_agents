# phase2-matching/tests/test_integration.py
import pytest
import os
import json
import sqlite3
from pathlib import Path
import sys

# Add phase2-matching to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import JobMatchingSystem
from config.scoring_config import SCORING_CONFIG

class TestJobMatchingSystem:
    """Integration tests for the complete job matching system."""
    
    def test_initialization(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db
    ):
        """Test system initialization."""
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False  # Disable AI for testing
        )
        
        assert system.resume_analysis is not None
        assert system.preferences is not None
        assert system.conn is not None
        assert system.scorer is not None
        assert system.explainer is not None
        
        system.close()
    
    def test_create_resume_text(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db
    ):
        """Test resume text creation."""
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False
        )
        
        resume_text = system.resume_text
        
        assert isinstance(resume_text, str)
        assert len(resume_text) > 0
        # Should contain job titles and skills
        assert "Job Titles:" in resume_text or "Skills:" in resume_text
        
        system.close()
    
    def test_match_jobs_limit(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db
    ):
        """Test matching jobs with limit."""
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False
        )
        
        scored_jobs = system.match_all_jobs(limit=2)
        
        assert len(scored_jobs) <= 2
        # All jobs should meet minimum threshold
        for job in scored_jobs:
            assert job.total_score >= SCORING_CONFIG['minimum_score_to_save']
        
        system.close()
    
    def test_match_all_jobs(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db,
        sample_jobs
    ):
        """Test matching all jobs."""
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False
        )
        
        scored_jobs = system.match_all_jobs()
        
        assert len(scored_jobs) > 0
        assert len(scored_jobs) <= len(sample_jobs)
        
        # Jobs should be sorted by score (descending)
        for i in range(len(scored_jobs) - 1):
            assert scored_jobs[i].total_score >= scored_jobs[i + 1].total_score
        
        system.close()
    
    def test_score_single_job(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db,
        sample_job
    ):
        """Test scoring a single job."""
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False
        )
        
        scored_job = system._score_single_job(sample_job)
        
        assert scored_job is not None
        assert scored_job.job_id == sample_job['job_id']
        assert scored_job.total_score > 0
        assert scored_job.total_score <= 100.0
        assert scored_job.grade in ["A+", "A", "B", "C", "D", "F"]
        assert scored_job.breakdown is not None
        assert scored_job.explanation is not None
        
        system.close()
    
    def test_save_results_to_json(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db,
        tmp_path
    ):
        """Test saving results to JSON file."""
        output_file = str(tmp_path / "test_results.json")
        
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False
        )
        
        scored_jobs = system.match_all_jobs()
        system.save_results(scored_jobs, output_file)
        
        # Verify file was created
        assert os.path.exists(output_file)
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == len(scored_jobs)
        
        system.close()
    
    def test_save_to_database(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db
    ):
        """Test saving results to database."""
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False
        )
        
        scored_jobs = system.match_all_jobs()
        system.save_to_database(scored_jobs)
        
        # Verify table was created
        cursor = system.conn.execute(
            "SELECT COUNT(*) FROM scored_jobs"
        )
        count = cursor.fetchone()[0]
        
        assert count == len(scored_jobs)
        
        system.close()
    
    def test_print_summary(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db,
        capsys
    ):
        """Test printing summary (captures output)."""
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False
        )
        
        scored_jobs = system.match_all_jobs()
        system.print_summary(scored_jobs)
        
        captured = capsys.readouterr()
        
        # Should print summary information
        assert "MATCHING SUMMARY" in captured.out or "Score Distribution" in captured.out
    
    def test_empty_database(
        self,
        temp_resume_file,
        temp_preferences_file,
        tmp_path
    ):
        """Test with empty database."""
        # Create empty database
        empty_db = str(tmp_path / "empty.db")
        conn = sqlite3.connect(empty_db)
        conn.execute("""
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
        conn.commit()
        conn.close()
        
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=empty_db,
            use_ai=False
        )
        
        scored_jobs = system.match_all_jobs()
        
        assert len(scored_jobs) == 0
        
        system.close()
    
    def test_filtering_by_minimum_score(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db
    ):
        """Test that jobs below minimum score are filtered out."""
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False
        )
        
        scored_jobs = system.match_all_jobs()
        
        min_score = SCORING_CONFIG['minimum_score_to_save']
        
        # All saved jobs should meet minimum threshold
        for job in scored_jobs:
            assert job.total_score >= min_score
        
        system.close()
    
    def test_system_cleanup(
        self,
        temp_resume_file,
        temp_preferences_file,
        temp_jobs_db
    ):
        """Test that system cleans up properly."""
        system = JobMatchingSystem(
            resume_analysis_path=temp_resume_file,
            preferences_path=temp_preferences_file,
            jobs_db_path=temp_jobs_db,
            use_ai=False
        )
        
        system.match_all_jobs()
        system.close()
        
        # Connection should be closed
        with pytest.raises(sqlite3.ProgrammingError):
            system.conn.execute("SELECT 1")


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_weights_sum_to_one(self):
        """Test that scoring weights sum to 1.0."""
        from config.scoring_config import SCORING_WEIGHTS
        
        total = sum(SCORING_WEIGHTS.values())
        
        assert total == pytest.approx(1.0, rel=0.01)
    
    def test_grade_thresholds_valid(self):
        """Test that grade thresholds are valid."""
        from config.scoring_config import GRADE_THRESHOLDS
        
        assert GRADE_THRESHOLDS['A+'] == 85
        assert GRADE_THRESHOLDS['A'] == 75
        assert GRADE_THRESHOLDS['B'] == 65
        assert GRADE_THRESHOLDS['C'] == 55
        assert GRADE_THRESHOLDS['D'] == 45
        assert GRADE_THRESHOLDS['F'] == 0
        
        # Should be in descending order
        assert GRADE_THRESHOLDS['A+'] > GRADE_THRESHOLDS['A']
        assert GRADE_THRESHOLDS['A'] > GRADE_THRESHOLDS['B']
        assert GRADE_THRESHOLDS['B'] > GRADE_THRESHOLDS['C']
    
    def test_recommendations_exist(self):
        """Test that all grades have recommendations."""
        from config.scoring_config import RECOMMENDATIONS
        
        for grade in ['A+', 'A', 'B', 'C', 'D', 'F']:
            assert grade in RECOMMENDATIONS
            assert len(RECOMMENDATIONS[grade]) > 0
    
    def test_config_values_reasonable(self):
        """Test that config values are reasonable."""
        assert SCORING_CONFIG['minimum_score_to_save'] >= 0
        assert SCORING_CONFIG['minimum_score_to_save'] <= 100
        assert SCORING_CONFIG['top_n_for_ai_analysis'] > 0
        assert SCORING_CONFIG['ai_batch_size'] > 0
