"""
Transform nested resume_analysis.json to flat format for Phase 2
"""
import json
from pathlib import Path

def transform_resume_analysis(nested_data: dict) -> dict:
    """
    Transform nested resume analysis to flat structure expected by Phase 2
    
    Phase 2 expects:
    - skills: List[str] (flat array)
    - job_titles: List[str]
    - experience_years: float
    - seniority: str (entry/mid/senior)
    - industries: List[str]
    - education: str
    - certifications: List[str]
    - search_queries: List[str]
    - alternative_titles: List[str]
    - priority_skills: List[str]
    """
    
    # 1. Extract all skills into flat array
    all_skills = []
    skills_data = nested_data.get('skills', {})
    
    # Handle nested skill categories
    for category, value in skills_data.items():
        if isinstance(value, list):
            # Direct list (e.g., "databases_and_caching": ["PostgreSQL", ...])
            all_skills.extend(value)
        elif isinstance(value, dict):
            # Nested dict (e.g., "programming_languages": {"expert": [...], "proficient": [...]})
            for sub_category, skill_list in value.items():
                if isinstance(skill_list, list):
                    all_skills.extend(skill_list)
    
    # Remove duplicates and clean up
    unique_skills = list(set(skill.strip() for skill in all_skills if skill.strip()))
    
    # 2. Extract job titles from experience
    job_titles = []
    experience_list = nested_data.get('experience', [])
    for exp in experience_list:
        title = exp.get('title', '').strip()
        if title:
            job_titles.append(title)
    
    # 3. Extract experience years from metadata
    metadata = nested_data.get('metadata', {})
    experience_years = float(metadata.get('total_years_experience', 0))
    
    # If not in metadata, estimate from experience count
    if experience_years == 0 and experience_list:
        experience_years = float(len(experience_list) * 2)  # Estimate 2 years per position
    
    # 4. Extract seniority level
    seniority = metadata.get('seniority_level', 'mid').lower()
    
    # Normalize seniority
    if 'senior' in seniority or 'lead' in seniority or 'principal' in seniority:
        seniority = 'senior'
    elif 'junior' in seniority or 'entry' in seniority or 'associate' in seniority:
        seniority = 'entry'
    else:
        seniority = 'mid'
    
    # 5. Extract education as string
    education_list = nested_data.get('education', [])
    education_str = "; ".join(
        edu.get('degree', '') for edu in education_list 
        if edu.get('degree')
    )
    
    # 6. Extract certifications
    certifications = []
    for cert in nested_data.get('certifications', []):
        if isinstance(cert, dict):
            cert_name = cert.get('name', '').strip()
            if cert_name:
                certifications.append(cert_name)
        elif isinstance(cert, str) and cert.strip():
            certifications.append(cert.strip())
    
    # 7. Generate search queries from job titles and top skills
    search_queries = []
    for title in job_titles[:3]:  # Top 3 titles
        search_queries.append(title)
        if unique_skills:
            # Add title + top skills combinations
            top_skills = unique_skills[:3]
            search_queries.append(f"{title} {' '.join(top_skills)}")
    
    # Add skill-only queries
    for skill in unique_skills[:5]:
        search_queries.append(f"{skill} Developer")
    
    # 8. Alternative titles (all titles except the first/main one)
    alternative_titles = job_titles[1:] if len(job_titles) > 1 else []
    
    # 9. Priority skills (top 10 skills based on position)
    # Prioritize: expert skills first, then proficient, then others
    priority_skills = unique_skills[:10]
    
    # 10. Determine industries from experience and skills
    industries = ['Technology', 'Software']  # Default
    # Could add more sophisticated industry detection based on experience
    
    # Build flat structure
    flat_data = {
        'skills': unique_skills,
        'job_titles': job_titles,
        'experience_years': experience_years,
        'seniority': seniority,
        'industries': industries,
        'education': education_str,
        'certifications': certifications,
        'search_queries': search_queries,
        'alternative_titles': alternative_titles,
        'priority_skills': priority_skills,
        # Keep optional fields
        'name': nested_data.get('personal_info', {}).get('name'),
        'email': nested_data.get('personal_info', {}).get('email'),
        'phone': nested_data.get('personal_info', {}).get('phone')
    }
    
    return flat_data


def main():
    """Transform the resume analysis file"""
    
    # Paths
    phase1_dir = Path(__file__).parent / 'phase1-scraping'
    input_file = phase1_dir / 'data' / 'resume_analysis.json'
    output_file = phase1_dir / 'data' / 'resume_analysis_flat.json'
    
    print("=" * 70)
    print("🔄 Resume Analysis Format Converter")
    print("=" * 70)
    
    # Read nested format
    print(f"\n📖 Reading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        nested_data = json.load(f)
    
    print(f"   ✓ Loaded nested format")
    print(f"   - Has skills object: {'skills' in nested_data}")
    print(f"   - Has experience array: {'experience' in nested_data}")
    print(f"   - Has metadata: {'metadata' in nested_data}")
    
    # Transform
    print("\n🔄 Transforming to flat format...")
    flat_data = transform_resume_analysis(nested_data)
    
    # Show transformation summary
    print("\n📊 Transformation Summary:")
    print(f"   ✓ Skills extracted: {len(flat_data['skills'])} skills")
    print(f"   ✓ Job titles: {len(flat_data['job_titles'])} titles")
    print(f"   ✓ Experience years: {flat_data['experience_years']}")
    print(f"   ✓ Seniority: {flat_data['seniority']}")
    print(f"   ✓ Education: {flat_data['education'][:50]}...")
    print(f"   ✓ Certifications: {len(flat_data['certifications'])} certs")
    print(f"   ✓ Search queries: {len(flat_data['search_queries'])} queries")
    print(f"   ✓ Priority skills: {len(flat_data['priority_skills'])} skills")
    
    # Save flat format
    print(f"\n💾 Saving to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(flat_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Saved flat format!")
    
    # Also overwrite the original file (so Phase 2 can use it directly)
    print(f"\n📝 Updating original file...")
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(flat_data, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Updated {input_file}")
    
    # Show sample of extracted data
    print("\n" + "=" * 70)
    print("📋 Sample Extracted Data:")
    print("=" * 70)
    print(f"\nSkills (first 10):")
    for skill in flat_data['skills'][:10]:
        print(f"   - {skill}")
    
    print(f"\nJob Titles:")
    for title in flat_data['job_titles']:
        print(f"   - {title}")
    
    print(f"\nSearch Queries (first 5):")
    for query in flat_data['search_queries'][:5]:
        print(f"   - {query}")
    
    print("\n" + "=" * 70)
    print("✅ Conversion complete! File is ready for Phase 2")
    print("=" * 70)


if __name__ == "__main__":
    main()
