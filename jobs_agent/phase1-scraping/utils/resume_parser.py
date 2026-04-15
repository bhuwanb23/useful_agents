# utils/resume_parser.py
import re
from typing import List, Dict, Optional
from pathlib import Path

class ResumeParser:
    """
    Parse resume markdown files and extract structured data
    """
    
    def __init__(self):
        # Common skill patterns
        self.skill_patterns = {
            'programming': r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin)\b',
            'frameworks': r'\b(React|Angular|Vue|Django|Flask|FastAPI|Spring|Express|Next\.js|Node\.js)\b',
            'databases': r'\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|DynamoDB|Cassandra|SQL Server)\b',
            'cloud': r'\b(AWS|Azure|GCP|Google Cloud|Kubernetes|Docker|Terraform|Jenkins)\b',
            'tools': r'\b(Git|GitHub|GitLab|Jira|CI/CD|Linux|Unix|Vim|VS Code)\b'
        }
    
    def parse_markdown(self, file_path: str) -> Dict:
        """
        Parse markdown resume and extract structured data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'raw_content': content,
            'name': self._extract_name(content),
            'email': self._extract_email(content),
            'phone': self._extract_phone(content),
            'skills': self._extract_skills(content),
            'experience': self._extract_experience(content),
            'education': self._extract_education(content),
            'certifications': self._extract_certifications(content),
            'links': self._extract_links(content)
        }
    
    def _extract_name(self, content: str) -> Optional[str]:
        """Extract name from first heading"""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else None
    
    def _extract_email(self, content: str) -> Optional[str]:
        """Extract email address"""
        match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        return match.group(0) if match else None
    
    def _extract_phone(self, content: str) -> Optional[str]:
        """Extract phone number"""
        match = re.search(r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}', content)
        return match.group(0) if match else None
    
    def _extract_skills(self, content: str) -> List[str]:
        """Extract technical skills"""
        skills = set()
        
        # Find skills section
        skills_section = re.search(
            r'##\s*(?:Skills|Technical Skills|Technologies)(.*?)(?=##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if skills_section:
            section_content = skills_section.group(1)
            
            # Extract from patterns
            for category, pattern in self.skill_patterns.items():
                matches = re.findall(pattern, section_content, re.IGNORECASE)
                skills.update(matches)
        
        return sorted(list(skills))
    
    def _extract_experience(self, content: str) -> List[Dict]:
        """Extract work experience"""
        experience = []
        
        # Find experience section
        exp_section = re.search(
            r'##\s*(?:Experience|Work Experience)(.*?)(?=##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if exp_section:
            section_content = exp_section.group(1)
            
            # Find job entries (### Title)
            jobs = re.findall(
                r'###\s*(.+?)\n(.*?)(?=###|\Z)',
                section_content,
                re.DOTALL
            )
            
            for title_line, description in jobs:
                # Parse title line: "Senior Developer @ Company | 2020 - 2023"
                parts = re.split(r'[@|]', title_line)
                
                job_data = {
                    'title': parts[0].strip() if len(parts) > 0 else '',
                    'company': parts[1].strip() if len(parts) > 1 else '',
                    'duration': parts[2].strip() if len(parts) > 2 else '',
                    'description': description.strip()
                }
                experience.append(job_data)
        
        return experience
    
    def _extract_education(self, content: str) -> List[Dict]:
        """Extract education"""
        education = []
        
        edu_section = re.search(
            r'##\s*Education(.*?)(?=##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if edu_section:
            section_content = edu_section.group(1)
            
            # Find degree entries
            degrees = re.findall(
                r'###\s*(.+?)\n(.*?)(?=###|\Z)',
                section_content,
                re.DOTALL
            )
            
            for degree_line, details in degrees:
                parts = re.split(r'[@|]', degree_line)
                
                edu_data = {
                    'degree': parts[0].strip() if len(parts) > 0 else '',
                    'institution': parts[1].strip() if len(parts) > 1 else '',
                    'year': parts[2].strip() if len(parts) > 2 else '',
                    'details': details.strip()
                }
                education.append(edu_data)
        
        return education
    
    def _extract_certifications(self, content: str) -> List[str]:
        """Extract certifications"""
        certs = []
        
        cert_section = re.search(
            r'##\s*Certifications?(.*?)(?=##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if cert_section:
            section_content = cert_section.group(1)
            
            # Find bullet points
            certs = re.findall(r'[-*]\s*(.+)', section_content)
            certs = [cert.strip() for cert in certs]
        
        return certs
    
    def _extract_links(self, content: str) -> Dict[str, str]:
        """Extract social/portfolio links"""
        links = {}
        
        # LinkedIn
        linkedin = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', content)
        if linkedin:
            links['linkedin'] = f"https://linkedin.com/in/{linkedin.group(1)}"
        
        # GitHub
        github = re.search(r'github\.com/([a-zA-Z0-9-]+)', content)
        if github:
            links['github'] = f"https://github.com/{github.group(1)}"
        
        # Portfolio
        portfolio = re.search(r'https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)', content)
        if portfolio:
            links['portfolio'] = portfolio.group(0)
        
        return links

# Example usage:
"""
parser = ResumeParser()
resume_data = parser.parse_markdown('data/resume.md')
print(f"Name: {resume_data['name']}")
print(f"Skills: {', '.join(resume_data['skills'])}")
print(f"Experience: {len(resume_data['experience'])} positions")
"""