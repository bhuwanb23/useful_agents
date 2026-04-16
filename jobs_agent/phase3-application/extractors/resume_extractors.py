"""
Resume Extractor - Uses AI to extract data from resume
"""

import google.generativeai as genai
from typing import Dict, Any
import json
import re
from pathlib import Path

from models.extracted_profile import (
    ExtractedProfile,
    ExtractedPersonalInfo,
    ExtractedProfessionalInfo,
    ExtractedSkills,
    ExtractedEducationInfo,
    ExtractionMetadata,
    ExtractedField,
    ExtractionSource,
    SkillWithYears,
    create_high_confidence_field,
    create_missing_field
)
from config.extraction_prompts import (
    RESUME_EXTRACTION_PROMPT,
    SKILL_YEARS_EXTRACTION_PROMPT
)
import time


class ResumeExtractor:
    """
    Extract structured data from resume using AI
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
    
    def extract_from_file(self, resume_path: str) -> ExtractedProfile:
        """
        Extract data from resume file (markdown or PDF)
        """
        resume_path = Path(resume_path)
        
        if not resume_path.exists():
            raise FileNotFoundError(f"Resume not found: {resume_path}")
        
        # Read resume
        if resume_path.suffix == ".md":
            resume_text = resume_path.read_text(encoding='utf-8')
        else:
            raise ValueError(f"Unsupported format: {resume_path.suffix}")
        
        return self.extract_from_text(resume_text, str(resume_path))
    
    def extract_from_text(
        self, 
        resume_text: str, 
        source_path: str = "unknown"
    ) -> ExtractedProfile:
        """
        Extract data from resume text
        """
        start_time = time.time()
        
        print("🔍 Extracting data from resume...")
        
        # Call AI
        prompt = RESUME_EXTRACTION_PROMPT.format(resume_text=resume_text)
        
        try:
            response = self.model.generate_content(prompt)
            extraction_time = time.time() - start_time
            
            # Parse JSON response
            extracted_data = self._parse_ai_response(response.text)
            
            # Convert to ExtractedProfile
            profile = self._convert_to_profile(
                extracted_data,
                resume_text,
                source_path,
                extraction_time
            )
            
            print(f"✓ Extraction complete in {extraction_time:.1f}s")
            print(f"  Overall confidence: {profile.metadata.overall_confidence*100:.1f}%")
            
            return profile
            
        except Exception as e:
            print(f"✗ Extraction failed: {e}")
            # Return empty profile with error
            return self._create_empty_profile(resume_text, source_path, str(e))
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """
        Parse AI JSON response
        """
        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response: {response_text[:500]}")
            return {}
    
    def _convert_to_profile(
        self,
        data: Dict,
        resume_text: str,
        source_path: str,
        extraction_time: float
    ) -> ExtractedProfile:
        """
        Convert extracted dict to ExtractedProfile
        """
        # Personal info
        personal_data = data.get("personal_info", {})
        personal_info = ExtractedPersonalInfo(
            first_name=self._create_field(personal_data.get("first_name")),
            last_name=self._create_field(personal_data.get("last_name")),
            full_name=self._create_field(personal_data.get("full_name")),
            email=self._create_field(personal_data.get("email")),
            phone=self._create_field(personal_data.get("phone")),
            city=self._create_field(personal_data.get("city")),
            state=self._create_field(personal_data.get("state")),
            country=self._create_field(personal_data.get("country")),
            linkedin_url=self._create_field(personal_data.get("linkedin_url")),
            github_url=self._create_field(personal_data.get("github_url")),
            portfolio_url=self._create_field(personal_data.get("portfolio_url"))
        )
        
        # Professional info
        prof_data = data.get("professional_info", {})
        professional_info = ExtractedProfessionalInfo(
            current_title=self._create_field(prof_data.get("current_title")),
            current_company=self._create_field(prof_data.get("current_company")),
            years_of_experience=self._create_field(prof_data.get("years_of_experience")),
            seniority_level=self._create_field(prof_data.get("seniority_level")),
            job_titles=self._create_field(prof_data.get("job_titles")),
            industries=self._create_field(prof_data.get("industries"))
        )
        
        # Skills
        skills_data = data.get("skills", {})
        skills = ExtractedSkills(
            all_skills=self._create_field(skills_data.get("all_skills")),
            programming_languages=self._create_field(skills_data.get("programming_languages")),
            frameworks=self._create_field(skills_data.get("frameworks")),
            top_skills=skills_data.get("all_skills", {}).get("value", [])[:10]
        )
        
        # Skills with years
        skills_years_data = skills_data.get("skills_with_years", {})
        for skill, data in skills_years_data.items():
            skills.skills_with_years[skill] = SkillWithYears(
                skill_name=skill,
                years=data.get("years", 0),
                confidence=data.get("confidence", 0.5),
                source=data.get("reasoning", "AI inference")
            )
        
        # Education
        edu_data = data.get("education", {})
        education = ExtractedEducationInfo(
            highest_degree=self._create_field(edu_data.get("highest_degree")),
            institution=self._create_field(edu_data.get("institution")),
            graduation_year=self._create_field(edu_data.get("graduation_year"))
        )
        
        # Calculate metadata
        metadata = self._calculate_metadata(
            personal_info,
            professional_info,
            skills,
            education,
            source_path,
            extraction_time
        )
        
        return ExtractedProfile(
            metadata=metadata,
            personal_info=personal_info,
            professional_info=professional_info,
            skills=skills,
            education=education,
            raw_resume_text=resume_text
        )
    
    def _create_field(self, field_data: Any) -> ExtractedField:
        """
        Create ExtractedField from AI response
        """
        if not field_data or not isinstance(field_data, dict):
            return create_missing_field()
        
        value = field_data.get("value")
        confidence = field_data.get("confidence", 0.0)
        source_str = field_data.get("source", "unknown")
        reasoning = field_data.get("reasoning")
        
        # Map source string to enum
        source_map = {
            "resume_header": ExtractionSource.RESUME_HEADER,
            "resume_contact": ExtractionSource.RESUME_CONTACT,
            "resume_experience": ExtractionSource.RESUME_EXPERIENCE,
            "resume_skills": ExtractionSource.RESUME_SKILLS,
            "resume_education": ExtractionSource.RESUME_EDUCATION,
            "resume_links": ExtractionSource.RESUME_LINKS,
            "ai_inference": ExtractionSource.AI_INFERENCE,
            "calculated": ExtractionSource.CALCULATED
        }
        
        source = source_map.get(source_str, ExtractionSource.AI_INFERENCE)
        
        return ExtractedField(
            value=value,
            confidence=confidence,
            source=source,
            extraction_method="ai",
            reasoning=reasoning
        )
    
    def _calculate_metadata(
        self,
        personal: ExtractedPersonalInfo,
        professional: ExtractedProfessionalInfo,
        skills: ExtractedSkills,
        education: ExtractedEducationInfo,
        source_path: str,
        extraction_time: float
    ) -> ExtractionMetadata:
        """
        Calculate extraction metadata and statistics
        """
        all_fields = []
        
        # Collect all fields
        for section in [personal, professional, education]:
            for field_name, field_value in section.__dict__.items():
                if isinstance(field_value, ExtractedField):
                    all_fields.append(field_value)
        
        # Count by confidence level
        high_conf = sum(1 for f in all_fields if f.confidence >= 0.90)
        medium_conf = sum(1 for f in all_fields if 0.70 <= f.confidence < 0.90)
        low_conf = sum(1 for f in all_fields if 0.50 <= f.confidence < 0.70)
        missing = sum(1 for f in all_fields if f.confidence < 0.50)
        
        # Calculate overall confidence
        confidences = [f.confidence for f in all_fields if f.has_value]
        overall_conf = sum(confidences) / len(confidences) if confidences else 0.0
        
        return ExtractionMetadata(
            resume_source=source_path,
            resume_format="markdown",
            ai_model=self.model_name,
            overall_confidence=overall_conf,
            total_fields_extracted=len(all_fields),
            high_confidence_fields=high_conf,
            medium_confidence_fields=medium_conf,
            low_confidence_fields=low_conf,
            missing_fields=missing,
            extraction_time_seconds=extraction_time
        )
    
    def _create_empty_profile(
        self,
        resume_text: str,
        source_path: str,
        error: str
    ) -> ExtractedProfile:
        """
        Create empty profile when extraction fails
        """
        metadata = ExtractionMetadata(
            resume_source=source_path,
            resume_format="markdown",
            overall_confidence=0.0,
            errors_encountered=[error]
        )
        
        return ExtractedProfile(
            metadata=metadata,
            raw_resume_text=resume_text
        )