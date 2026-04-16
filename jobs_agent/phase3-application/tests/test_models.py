"""
Tests for data models
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.user_profile import UserProfile, PersonalInfo, ProfessionalInfo, SkillSet, Education
from models.learned_question import LearnedQuestion, QuestionType, AnswerStrategy
from models.application import Application, ApplicationStatus, ApplicationMethod
from models.form_field import FormField, FieldType, FieldCategory


def test_user_profile():
    """Test UserProfile model"""
    print("\n" + "=" * 70)
    print("Testing UserProfile Model")
    print("=" * 70)
    
    personal = PersonalInfo(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+1-555-0123",
        city="San Francisco",
        state="CA",
        country="USA"
    )
    
    professional = ProfessionalInfo(
        current_title="Senior Software Engineer",
        current_company="TechCorp",
        years_of_experience=5,
        seniority_level="senior",
        job_titles=["Software Engineer", "Backend Developer"],
        industries=["SaaS", "Tech"]
    )
    
    skills = SkillSet(
        all_skills=["Python", "JavaScript", "React"],
        programming_languages=["Python", "JavaScript"],
        frameworks=["React", "FastAPI"],
        top_skills=["Python", "React"]
    )
    
    education = [Education(
        degree="Bachelor of Science in Computer Science",
        institution="University of Tech",
        graduation_year=2018
    )]
    
    from models.user_profile import LegalInfo, SalaryExpectations, Documents, WorkAuthorization
    
    profile = UserProfile(
        personal_info=personal,
        professional_info=professional,
        skills=skills,
        education=education,
        legal_info=LegalInfo(
            work_authorization=WorkAuthorization.US_CITIZEN,
            requires_sponsorship=False
        ),
        salary_expectations=SalaryExpectations(
            min_salary=120000,
            max_salary=180000
        ),
        documents=Documents(
            resume_path="data/resume.pdf"
        )
    )
    
    print(f"✓ Created profile for: {profile.personal_info.full_name}")
    print(f"  Email: {profile.personal_info.email}")
    print(f"  Title: {profile.professional_info.current_title}")
    print(f"  Experience: {profile.professional_info.years_of_experience} years")
    print(f"  Skills: {len(profile.skills.all_skills)}")
    
    # Test application data export
    app_data = profile.get_application_data()
    print(f"\n✓ Application data has {len(app_data)} fields")
    print(f"  Sample: {list(app_data.keys())[:5]}")


def test_learned_question():
    """Test LearnedQuestion model"""
    print("\n" + "=" * 70)
    print("Testing LearnedQuestion Model")
    print("=" * 70)
    
    question = LearnedQuestion(
        question_text="How many years of Python experience do you have?",
        normalized_question="years python experience",
        question_type=QuestionType.YEARS_EXPERIENCE,
        answer_strategy=AnswerStrategy.AUTO,
        answer_value="5 years",
        answer_source="user_profile.skills.skills_with_years.Python"
    )
    
    print(f"✓ Created learned question")
    print(f"  Type: {question.question_type}")
    print(f"  Strategy: {question.answer_strategy}")
    print(f"  Answer: {question.answer_value}")
    
    # Simulate encounters
    question.update_encounter()
    question.mark_successful()
    
    print(f"\n✓ Updated statistics")
    print(f"  Encountered: {question.encountered_count} times")
    print(f"  Success rate: {question.success_rate * 100:.0f}%")
    print(f"  Is reliable: {question.is_reliable}")


def test_application():
    """Test Application model"""
    print("\n" + "=" * 70)
    print("Testing Application Model")
    print("=" * 70)
    
    app = Application(
        job_id="job_123",
        company="TechCorp",
        title="Senior Python Engineer",
        job_url="https://example.com/job/123",
        match_score=87.5,
        grade="A+",
        application_method=ApplicationMethod.LINKEDIN_EASY_APPLY,
        status=ApplicationStatus.PREPARED,
        cover_letter_text="Dear Hiring Manager...",
        resume_used="data/resume.pdf"
    )
    
    print(f"✓ Created application")
    print(f"  Company: {app.company}")
    print(f"  Title: {app.title}")
    print(f"  Match Score: {app.match_score}")
    print(f"  Status: {app.status}")
    
    # Mark as submitted
    app.mark_submitted()
    print(f"\n✓ Marked as submitted")
    print(f"  Applied: {app.applied_date}")
    print(f"  Status: {app.status}")


def test_form_field():
    """Test FormField model"""
    print("\n" + "=" * 70)
    print("Testing FormField Model")
    print("=" * 70)
    
    field = FormField(
        field_id="first_name_input",
        label="First Name",
        input_type=FieldType.TEXT,
        field_category=FieldCategory.PERSONAL_INFO,
        required=True,
        matched_to="user_profile.personal_info.first_name",
        confidence=0.95
    )
    
    print(f"✓ Created form field")
    print(f"  Label: {field.label}")
    print(f"  Type: {field.input_type}")
    print(f"  Category: {field.field_category}")
    print(f"  Required: {field.required}")
    print(f"  Matched to: {field.matched_to}")
    print(f"  Confidence: {field.confidence * 100:.0f}%")
    print(f"  Is simple: {field.is_simple}")


if __name__ == "__main__":
    test_user_profile()
    test_learned_question()
    test_application()
    test_form_field()
    
    print("\n" + "=" * 70)
    print("✅ All model tests passed!")
    print("=" * 70)