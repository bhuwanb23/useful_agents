"""
Confidence Calculator - Validates and adjusts confidence scores
"""

from typing import Dict, List
import re
from models.extracted_profile import ExtractedField, ExtractedProfile


class ConfidenceCalculator:
    """
    Calculate and validate confidence scores for extracted data
    """
    
    # Patterns for high-confidence validation
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Z|a-z]{2,}$'
    PHONE_PATTERN = r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$'
    URL_PATTERN = r'^https?://[^\s]+$'
    
    def __init__(self):
        pass
    
    def validate_and_adjust(self, profile: ExtractedProfile) -> ExtractedProfile:
        """
        Validate extracted data and adjust confidence scores
        """
        print("\n🔍 Validating extracted data...")
        
        # Validate personal info
        self._validate_personal_info(profile.personal_info)
        
        # Validate professional info
        self._validate_professional_info(profile.professional_info)
        
        # Validate skills
        self._validate_skills(profile.skills)
        
        # Recalculate overall confidence
        profile.metadata = self._recalculate_metadata(profile)
        
        print(f"✓ Validation complete")
        print(f"  Adjusted overall confidence: {profile.metadata.overall_confidence*100:.1f}%")
        
        return profile
    
    def _validate_personal_info(self, personal_info):
        """Validate personal information fields"""
        
        # Email validation
        if personal_info.email.value:
            if re.match(self.EMAIL_PATTERN, personal_info.email.value):
                personal_info.email.confidence = max(personal_info.email.confidence, 0.95)
            else:
                personal_info.email.confidence = min(personal_info.email.confidence, 0.60)
                personal_info.email.needs_review = True
        
        # Phone validation
        if personal_info.phone.value:
            cleaned_phone = re.sub(r'[^\d+]', '', personal_info.phone.value)
            if len(cleaned_phone) >= 10:
                personal_info.phone.confidence = max(personal_info.phone.confidence, 0.85)
            else:
                personal_info.phone.confidence = min(personal_info.phone.confidence, 0.60)
        
        # URL validations
        for url_field in [personal_info.linkedin_url, personal_info.github_url, 
                          personal_info.portfolio_url]:
            if url_field.value:
                if re.match(self.URL_PATTERN, str(url_field.value)):
                    url_field.confidence = max(url_field.confidence, 0.95)
                else:
                    url_field.confidence = min(url_field.confidence, 0.50)
        
        # Name validation (should not be empty)
        if personal_info.first_name.value and len(personal_info.first_name.value) >= 2:
            personal_info.first_name.confidence = max(personal_info.first_name.confidence, 0.90)
        
        if personal_info.last_name.value and len(personal_info.last_name.value) >= 2:
            personal_info.last_name.confidence = max(personal_info.last_name.confidence, 0.90)
    
    def _validate_professional_info(self, prof_info):
        """Validate professional information"""
        
        # Years of experience should be reasonable (0-50)
        if prof_info.years_of_experience.value:
            years = prof_info.years_of_experience.value
            if 0 <= years <= 50:
                prof_info.years_of_experience.confidence = max(
                    prof_info.years_of_experience.confidence, 0.85
                )
            else:
                prof_info.years_of_experience.confidence = 0.30
                prof_info.years_of_experience.needs_review = True
        
        # Title and company should not be empty
        if prof_info.current_title.value and len(prof_info.current_title.value) > 3:
            prof_info.current_title.confidence = max(prof_info.current_title.confidence, 0.85)
    
    def _validate_skills(self, skills):
        """Validate skills data"""
        
        # Skills list should not be empty
        if skills.all_skills.value and len(skills.all_skills.value) > 0:
            skills.all_skills.confidence = max(skills.all_skills.confidence, 0.85)
        
        # Validate years per skill
        for skill_name, skill_data in skills.skills_with_years.items():
            if 0 <= skill_data.years <= 50:
                skill_data.confidence = max(skill_data.confidence, 0.80)
            else:
                skill_data.confidence = 0.40
    
    def _recalculate_metadata(self, profile: ExtractedProfile):
        """Recalculate metadata after validation"""
        
        all_fields = []
        
        # Collect all fields
        for section in [profile.personal_info, profile.professional_info, profile.education]:
            for field_name, field_value in section.__dict__.items():
                if isinstance(field_value, ExtractedField):
                    all_fields.append(field_value)
        
        # Recount by confidence level
        high_conf = sum(1 for f in all_fields if f.confidence >= 0.90)
        medium_conf = sum(1 for f in all_fields if 0.70 <= f.confidence < 0.90)
        low_conf = sum(1 for f in all_fields if 0.50 <= f.confidence < 0.70)
        missing = sum(1 for f in all_fields if f.confidence < 0.50)
        
        # Recalculate overall confidence
        confidences = [f.confidence for f in all_fields if f.has_value]
        overall_conf = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Update metadata
        profile.metadata.overall_confidence = overall_conf
        profile.metadata.high_confidence_fields = high_conf
        profile.metadata.medium_confidence_fields = medium_conf
        profile.metadata.low_confidence_fields = low_conf
        profile.metadata.missing_fields = missing
        
        return profile.metadata
    
    def get_validation_report(self, profile: ExtractedProfile) -> Dict:
        """
        Get detailed validation report
        """
        report = {
            "valid_fields": [],
            "needs_review": [],
            "invalid_fields": [],
            "missing_fields": []
        }
        
        for section_name, section in [
            ("personal_info", profile.personal_info),
            ("professional_info", profile.professional_info),
            ("education", profile.education)
        ]:
            for field_name, field_value in section.__dict__.items():
                if isinstance(field_value, ExtractedField):
                    full_name = f"{section_name}.{field_name}"
                    
                    if not field_value.has_value:
                        report["missing_fields"].append(full_name)
                    elif field_value.confidence >= 0.90:
                        report["valid_fields"].append(full_name)
                    elif field_value.confidence >= 0.50:
                        report["needs_review"].append(full_name)
                    else:
                        report["invalid_fields"].append(full_name)
        
        return report