# phase2-matching/tests/test_utils.py
import pytest
from utils.skill_extractor import SkillExtractor
from utils.explainer import MatchExplainer
from models.scored_job import ScoreBreakdown, MatchExplanation

class TestSkillExtractor:
    """Test skill extraction from text."""
    
    def test_extract_programming_languages(self):
        """Test extracting programming languages."""
        extractor = SkillExtractor()
        
        text = "We need Python, JavaScript, Java, and C++ developers"
        skills = extractor.extract_skills(text)
        
        assert 'python' in skills
        assert 'javascript' in skills
        assert 'java' in skills
        assert 'c++' in skills
    
    def test_extract_frameworks(self):
        """Test extracting frameworks."""
        extractor = SkillExtractor()
        
        text = "Experience with React, Django, Flask, and FastAPI required"
        skills = extractor.extract_skills(text)
        
        assert 'react' in skills
        assert 'django' in skills
        assert 'flask' in skills
        assert 'fastapi' in skills
    
    def test_extract_databases(self):
        """Test extracting database technologies."""
        extractor = SkillExtractor()
        
        text = "Work with PostgreSQL, MongoDB, Redis, and Elasticsearch"
        skills = extractor.extract_skills(text)
        
        assert 'postgresql' in skills
        assert 'mongodb' in skills
        assert 'redis' in skills
        assert 'elasticsearch' in skills
    
    def test_extract_cloud_technologies(self):
        """Test extracting cloud technologies."""
        extractor = SkillExtractor()
        
        text = "AWS, Azure, Docker, Kubernetes, and Terraform experience needed"
        skills = extractor.extract_skills(text)
        
        assert 'aws' in skills
        assert 'docker' in skills
        assert 'kubernetes' in skills
        assert 'terraform' in skills
    
    def test_skill_alias_normalization(self):
        """Test skill alias normalization."""
        extractor = SkillExtractor()
        
        text = "Need JS, ReactJS, Node, and Postgres experience"
        skills = extractor.extract_skills(text)
        
        # Should normalize aliases
        assert 'javascript' in skills  # JS -> JavaScript
        assert 'react' in skills  # ReactJS -> React
        assert 'node.js' in skills  # Node -> Node.js
        assert 'postgresql' in skills  # Postgres -> PostgreSQL
    
    def test_extract_from_bullet_list(self):
        """Test extracting skills from bullet list."""
        extractor = SkillExtractor()
        
        text = """
        Required skills:
        - Python and Django
        - PostgreSQL and Redis
        - AWS and Docker
        - Git and CI/CD
        """
        
        skills = extractor.extract_from_list(text)
        
        assert len(skills) > 0
        assert 'python' in skills or 'django' in skills
    
    def test_empty_text(self):
        """Test extracting from empty text."""
        extractor = SkillExtractor()
        
        skills = extractor.extract_skills("")
        
        assert skills == []
    
    def test_no_skills_in_text(self):
        """Test text with no recognizable skills."""
        extractor = SkillExtractor()
        
        text = "We need someone who is hardworking and motivated"
        skills = extractor.extract_skills(text)
        
        assert skills == []
    
    def test_calculate_overlap(self):
        """Test skill overlap calculation."""
        extractor = SkillExtractor()
        
        skills1 = ["Python", "JavaScript", "React"]
        skills2 = ["Python", "React", "Django"]
        
        overlap = extractor.calculate_overlap(skills1, skills2)
        
        # 2 out of 3 skills overlap
        assert overlap == pytest.approx(0.666, rel=0.01)
    
    def test_find_missing_skills(self):
        """Test finding missing skills."""
        extractor = SkillExtractor()
        
        candidate_skills = ["Python", "JavaScript", "React"]
        required_skills = ["Python", "React", "Django", "PostgreSQL"]
        
        missing = extractor.find_missing(candidate_skills, required_skills)
        
        assert 'django' in missing
        assert 'postgresql' in missing
        assert 'python' not in missing  # Not missing
        assert 'react' not in missing  # Not missing


class TestMatchExplainer:
    """Test match explanation generation."""
    
    def test_score_to_grade_a_plus(self):
        """Test A+ grade conversion."""
        explainer = MatchExplainer()
        
        grade = explainer.score_to_grade(90)
        
        assert grade == "A+"
    
    def test_score_to_grade_a(self):
        """Test A grade conversion."""
        explainer = MatchExplainer()
        
        grade = explainer.score_to_grade(80)
        
        assert grade == "A"
    
    def test_score_to_grade_b(self):
        """Test B grade conversion."""
        explainer = MatchExplainer()
        
        grade = explainer.score_to_grade(70)
        
        assert grade == "B"
    
    def test_score_to_grade_c(self):
        """Test C grade conversion."""
        explainer = MatchExplainer()
        
        grade = explainer.score_to_grade(60)
        
        assert grade == "C"
    
    def test_score_to_grade_d(self):
        """Test D grade conversion."""
        explainer = MatchExplainer()
        
        grade = explainer.score_to_grade(50)
        
        assert grade == "D"
    
    def test_score_to_grade_f(self):
        """Test F grade conversion."""
        explainer = MatchExplainer()
        
        grade = explainer.score_to_grade(30)
        
        assert grade == "F"
    
    def test_create_explanation(self):
        """Test creating match explanation."""
        explainer = MatchExplainer()
        
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
        
        explanation = explainer.create_explanation(
            breakdown=breakdown,
            total_score=81.0,
            ai_summary="Great match!",
            missing_skills=["Kubernetes"]
        )
        
        assert isinstance(explanation, MatchExplanation)
        assert len(explanation.strengths) > 0
        assert explanation.recommendation != ""
    
    def test_explanation_with_concerns(self):
        """Test explanation includes concerns for low scores."""
        explainer = MatchExplainer()
        
        breakdown = ScoreBreakdown(
            skills_match=10.0,  # Low
            experience_match=5.0,  # Low
            title_match=8.0,
            semantic_similarity=5.0,
            salary_match=3.0,  # Low
            location_match=2.0,  # Low
            culture_fit=2.0,
            growth_potential=2.0
        )
        
        explanation = explainer.create_explanation(
            breakdown=breakdown,
            total_score=37.0,
            missing_skills=["Python", "Django", "AWS"]
        )
        
        assert len(explanation.concerns) > 0


class TestEmbeddingCache:
    """Test embedding cache functionality."""
    
    def test_cache_set_and_get(self, sample_embedding_cache):
        """Test setting and getting cached embeddings."""
        cache = sample_embedding_cache
        
        cache.set("test_key", [0.1, 0.2, 0.3])
        result = cache.get("test_key")
        
        assert result == [0.1, 0.2, 0.3]
    
    def test_cache_get_nonexistent(self, sample_embedding_cache):
        """Test getting non-existent cache entry."""
        cache = sample_embedding_cache
        
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_cache_save_and_load(self, sample_embedding_cache, tmp_path):
        """Test cache save and load."""
        # This test would require actual EmbeddingCache implementation
        # For now, just test that methods exist
        cache = sample_embedding_cache
        
        cache.set("key1", [0.1, 0.2])
        cache.save()
        cache.load()
        
        # Should not raise exception
        assert cache.get("key1") == [0.1, 0.2]
