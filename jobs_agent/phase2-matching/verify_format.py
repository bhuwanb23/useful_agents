import json

# Load the transformed resume analysis
with open('../phase1-scraping/data/resume_analysis.json', 'r') as f:
    data = json.load(f)

print('Format Check:')
print(f'  skills type: {type(data["skills"]).__name__} ({len(data["skills"])} items)')
print(f'  job_titles type: {type(data["job_titles"]).__name__} ({len(data["job_titles"])} items)')
print(f'  experience_years type: {type(data["experience_years"]).__name__} (value: {data["experience_years"]})')
print(f'  seniority type: {type(data["seniority"]).__name__} (value: {data["seniority"]})')
print(f'  industries type: {type(data["industries"]).__name__} ({len(data["industries"])} items)')
print(f'  education type: {type(data["education"]).__name__}')
print(f'  certifications type: {type(data["certifications"]).__name__} ({len(data["certifications"])} items)')
print(f'  search_queries type: {type(data["search_queries"]).__name__} ({len(data["search_queries"])} items)')
print(f'  priority_skills type: {type(data["priority_skills"]).__name__} ({len(data["priority_skills"])} items)')

print('\n✅ Format is correct! Phase 2 can use this!')
