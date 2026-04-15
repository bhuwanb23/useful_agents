# phase2-matching/tests/test_matchers.py
import pytest
from matchers.skill_matcher import SkillMatcher
from matchers.experience_matcher import ExperienceMatcher
from matchers.title_matcher import TitleMatcher
from matchers.salary_matcher import SalaryMatcher
from matchers.location_matcher import LocationMatcher

class TestSkillMatcher:
    """Test skill matching functionality."""
    
    def test_exact_skill_match(self, sample_skill_text):
        """Test exact skill matches."""
        matcher = SkillMatcher()
        resume_skills = ["Python", "JavaScript", "React", "PostgreSQL"]
        
        score = matcher.calculate_match(
            resume_skills=resume_skills,
            job_description=sample_skill_text,
            max_score=30.0
        )
        
        assert score > 0
        assert score <= 30.0
    
    def test_partial_skill_match(self):
        """Test partial skill matches."""
        matcher = SkillMatcher()
        resume_skills = ["Python", "Java"]  # Only Python matches
        job_desc = "Looking for Python developer with Django experience"
        
        score = matcher.calculate_match(
            resume_skills=resume_skills,
            job_description=job_desc,
            max_score=30.0
        )
        
        assert score > 0
        assert score < 30.0
    
    def test_no_skill_match(self):
        """Test when no skills match."""
        matcher = SkillMatcher()
        resume_skills = ["Photoshop", "Illustrator"]  # Design skills, not tech
        job_desc = "Looking for Python, Django, PostgreSQL developer"
        
        score = matcher.calculate_match(
            resume_skills=resume_skills,
            job_description=job_desc,
            max_score=30.0
        )
        
        # Should get neutral score (50%) since can extract job skills
        assert score >= 10.0
        assert score <= 20.0
    
    def test_fuzzy_skill_matching(self):
        """Test fuzzy matching for similar skills."""
        matcher = SkillMatcher(fuzzy_threshold=0.85)
        resume_skills = ["PostgreSQL", "JavaScript", "ReactJS"]
        job_desc = "Need Postgres, Javascript, and React expertise"
        
        score = matcher.calculate_match(
            resume_skills=resume_skills,
            job_description=job_desc,
            max_score=30.0
        )
        
        assert score > 0
    
    def test_skill_density_bonus(self):
        """Test that having many skills gives density bonus."""
        matcher = SkillMatcher()
        resume_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Django",
            "FastAPI", "PostgreSQL", "MongoDB", "Redis", "AWS",
            "Docker", "Kubernetes", "Git", "CI/CD", "REST APIs"
        ]
        job_desc = "Python developer needed with web development skills"
        
        score_many = matcher.calculate_match(
            resume_skills=resume_skills,
            job_description=job_desc,
            max_score=30.0
        )
        
        resume_skills_few = ["Python"]
        score_few = matcher.calculate_match(
            resume_skills=resume_skills_few,
            job_description=job_desc,
            max_score=30.0
        )
        
        # More skills should generally score higher
        assert score_many >= score_few
    
    def test_get_matched_skills(self, sample_skill_text):
        """Test getting detailed skill match info."""
        matcher = SkillMatcher()
        resume_skills = ["Python", "JavaScript", "React", "PostgreSQL", "AWS"]
        
        result = matcher.get_matched_skills(
            resume_skills=resume_skills,
            job_description=sample_skill_text
        )
        
        assert 'matched_skills' in result
        assert 'missing_skills' in result
        assert 'match_rate' in result
        assert 'total_job_skills' in result
        assert 'total_resume_skills' in result
        assert len(result['matched_skills']) > 0
    
    def test_empty_job_description(self):
        """Test handling of empty job description."""
        matcher = SkillMatcher()
        
        score = matcher.calculate_match(
            resume_skills=["Python", "JavaScript"],
            job_description="",
            max_score=30.0
        )
        
        # Should return neutral score
        assert score == 15.0
    
    def test_empty_resume_skills(self, sample_skill_text):
        """Test handling of empty resume skills."""
        matcher = SkillMatcher()
        
        score = matcher.calculate_match(
            resume_skills=[],
            job_description=sample_skill_text,
            max_score=30.0
        )
        
        assert score >= 0
        assert score < 15.0  # Should be low


class TestExperienceMatcher:
    """Test experience matching functionality."""
    
    def test_exact_experience_match(self):
        """Test when experience matches exactly."""
        matcher = ExperienceMatcher()
        
        score = matcher.calculate_match(
            resume_years=5,
            resume_seniority="senior",
            job_title="Senior Python Developer",
            job_description="5+ years experience required",
            max_score=15.0
        )
        
        assert score > 10.0  # Should be high match
    
    def test_underqualified(self):
        """Test when candidate has less experience."""
        matcher = ExperienceMatcher()
        
        score = matcher.calculate_match(
            resume_years=2,
            resume_seniority="junior",
            job_title="Senior Python Developer",
            job_description="8+ years experience required",
            max_score=15.0
        )
        
        assert score < 10.0
    
    def test_overqualified(self):
        """Test when candidate has more experience."""
        matcher = ExperienceMatcher()
        
        score = matcher.calculate_match(
            resume_years=10,
            resume_seniority="senior",
            job_title="Junior Developer",
            job_description="1-2 years experience",
            max_score=15.0
        )
        
        # Should still score reasonably but with penalty
        assert score > 0
        assert score < 15.0
    
    def test_seniority_mismatch(self):
        """Test seniority level mismatch."""
        matcher = ExperienceMatcher()
        
        score = matcher.calculate_match(
            resume_years=5,
            resume_seniority="senior",
            job_title="Intern Developer",
            job_description="No experience required",
            max_score=15.0
        )
        
        assert score < 10.0
    
    def test_experience_from_description(self):
        """Test extracting years from job description."""
        matcher = ExperienceMatcher()
        
        score = matcher.calculate_match(
            resume_years=5,
            resume_seniority="mid",
            job_title="Python Developer",
            job_description="Looking for developer with 4-6 years of experience",
            max_score=15.0
        )
        
        assert score > 10.0
    
    def test_no_experience_info(self):
        """Test when no experience info in job."""
        matcher = ExperienceMatcher()
        
        score = matcher.calculate_match(
            resume_years=5,
            resume_seniority="senior",
            job_title="Developer",
            job_description="Join our team!",
            max_score=15.0
        )
        
        # Should give neutral score
        assert score > 0


class TestTitleMatcher:
    """Test job title matching functionality."""
    
    def test_exact_title_match(self):
        """Test exact title match."""
        matcher = TitleMatcher()
        
        score = matcher.calculate_match(
            resume_titles=["Senior Python Developer"],
            job_title="Senior Python Developer",
            max_score=15.0
        )
        
        assert score == 15.0
    
    def test_similar_title_match(self):
        """Test similar title match."""
        matcher = TitleMatcher()
        
        score = matcher.calculate_match(
            resume_titles=["Software Engineer"],
            job_title="Senior Software Engineer",
            max_score=15.0
        )
        
        assert score > 10.0
    
    def test_partial_title_match(self):
        """Test partial title match."""
        matcher = TitleMatcher()
        
        score = matcher.calculate_match(
            resume_titles=["Python Developer"],
            job_title="Senior Python Developer",
            max_score=15.0
        )
        
        assert score > 8.0
    
    def test_no_title_match(self):
        """Test no title match."""
        matcher = TitleMatcher()
        
        score = matcher.calculate_match(
            resume_titles=["Data Scientist"],
            job_title="Frontend Designer",
            max_score=15.0
        )
        
        assert score < 5.0
    
    def test_multiple_resume_titles(self):
        """Test matching against multiple resume titles."""
        matcher = TitleMatcher()
        
        score = matcher.calculate_match(
            resume_titles=["Backend Engineer", "Python Developer", "Software Architect"],
            job_title="Senior Python Engineer",
            max_score=15.0
        )
        
        assert score > 10.0


class TestSalaryMatcher:
    """Test salary matching functionality."""
    
    def test_salary_in_range(self):
        """Test when salary is in expected range."""
        matcher = SalaryMatcher()
        
        score = matcher.calculate_match(
            min_expected=100000,
            job_min=120000,
            job_max=150000,
            max_score=10.0
        )
        
        assert score > 7.0
    
    def test_salary_below_range(self):
        """Test when salary is below expected."""
        matcher = SalaryMatcher()
        
        score = matcher.calculate_match(
            min_expected=100000,
            job_min=70000,
            job_max=90000,
            max_score=10.0
        )
        
        assert score < 5.0
    
    def test_salary_above_range(self):
        """Test when salary is above expected (bonus)."""
        matcher = SalaryMatcher()
        
        score = matcher.calculate_match(
            min_expected=100000,
            job_min=150000,
            job_max=180000,
            max_score=10.0
        )
        
        assert score > 8.0
    
    def test_no_salary_info(self):
        """Test when no salary info provided."""
        matcher = SalaryMatcher()
        
        score = matcher.calculate_match(
            min_expected=100000,
            job_min=None,
            job_max=None,
            max_score=10.0
        )
        
        # Should give neutral score
        assert score == 5.0
    
    def test_partial_salary_info(self):
        """Test when only partial salary info."""
        matcher = SalaryMatcher()
        
        score = matcher.calculate_match(
            min_expected=100000,
            job_min=110000,
            job_max=None,
            max_score=10.0
        )
        
        assert score > 5.0
    
    def test_no_expected_salary(self):
        """Test when no expected salary."""
        matcher = SalaryMatcher()
        
        score = matcher.calculate_match(
            min_expected=None,
            job_min=100000,
            job_max=130000,
            max_score=10.0
        )
        
        # Should give neutral score
        assert score == 5.0


class TestLocationMatcher:
    """Test location matching functionality."""
    
    def test_remote_match(self):
        """Test remote job when remote preferred."""
        matcher = LocationMatcher()
        
        score = matcher.calculate_match(
            preferred_locations=["United States"],
            remote_only=True,
            job_location="Remote",
            job_is_remote=True,
            max_score=5.0
        )
        
        assert score == 5.0
    
    def test_location_match(self):
        """Test location match."""
        matcher = LocationMatcher()
        
        score = matcher.calculate_match(
            preferred_locations=["San Francisco", "Remote"],
            remote_only=False,
            job_location="San Francisco, CA",
            job_is_remote=False,
            max_score=5.0
        )
        
        assert score == 5.0
    
    def test_location_mismatch(self):
        """Test location mismatch."""
        matcher = LocationMatcher()
        
        score = matcher.calculate_match(
            preferred_locations=["New York"],
            remote_only=False,
            job_location="London, UK",
            job_is_remote=False,
            max_score=5.0
        )
        
        assert score < 3.0
    
    def test_remote_required_but_not_offered(self):
        """Test when remote required but job is onsite."""
        matcher = LocationMatcher()
        
        score = matcher.calculate_match(
            preferred_locations=["United States"],
            remote_only=True,
            job_location="New York, NY",
            job_is_remote=False,
            max_score=5.0
        )
        
        assert score < 2.0
    
    def test_no_location_preference(self):
        """Test when no location preference."""
        matcher = LocationMatcher()
        
        score = matcher.calculate_match(
            preferred_locations=[],
            remote_only=False,
            job_location="Anywhere",
            job_is_remote=True,
            max_score=5.0
        )
        
        # Should give neutral or good score
        assert score >= 2.5
