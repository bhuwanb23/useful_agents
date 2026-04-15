# phase2-matching/utils/skill_extractor.py
import re
from typing import List, Set

class SkillExtractor:
    """
    Extract technical skills from text
    """
    
    # Common skill patterns
    SKILL_PATTERNS = {
        'programming': r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin|Scala|R|MATLAB)\b',
        'frameworks': r'\b(React|Angular|Vue|Svelte|Django|Flask|FastAPI|Spring|Express|Next\.js|Node\.js|Rails|Laravel|\.NET)\b',
        'databases': r'\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|DynamoDB|Cassandra|SQL Server|Oracle|SQLite|MariaDB)\b',
        'cloud': r'\b(AWS|Azure|GCP|Google Cloud|Kubernetes|Docker|Terraform|Ansible|Jenkins|CircleCI|GitHub Actions)\b',
        'data': r'\b(Pandas|NumPy|Scikit-learn|TensorFlow|PyTorch|Spark|Hadoop|Airflow|Kafka|Tableau|Power BI)\b',
        'mobile': r'\b(iOS|Android|React Native|Flutter|SwiftUI|Jetpack Compose)\b',
        'other': r'\b(Git|GitHub|GitLab|Linux|Unix|Bash|SQL|NoSQL|REST|GraphQL|gRPC|Microservices|CI/CD|Agile|Scrum)\b'
    }
    
    # Common skill aliases
    SKILL_ALIASES = {
        'js': 'javascript',
        'ts': 'typescript',
        'reactjs': 'react',
        'react.js': 'react',
        'nodejs': 'node.js',
        'node': 'node.js',
        'postgres': 'postgresql',
        'k8s': 'kubernetes',
        'ml': 'machine learning',
        'ai': 'artificial intelligence',
    }
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract all skills from text
        """
        if not text:
            return []
        
        skills = set()
        text_lower = text.lower()
        
        # Extract using patterns
        for category, pattern in self.SKILL_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update([m.lower() for m in matches])
        
        # Normalize aliases
        normalized = set()
        for skill in skills:
            normalized_skill = self.SKILL_ALIASES.get(skill.lower(), skill.lower())
            normalized.add(normalized_skill)
        
        return sorted(list(normalized))
    
    def extract_from_list(self, text: str) -> List[str]:
        """
        Extract skills from bullet-point list (common in job descriptions)
        """
        skills = []
        
        # Find bullet points
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*', '·')):
                # Remove bullet
                line = re.sub(r'^[-•*·]\s*', '', line)
                # Extract skills from this line
                line_skills = self.extract_skills(line)
                skills.extend(line_skills)
        
        return list(set(skills))
    
    def calculate_overlap(self, skills1: List[str], skills2: List[str]) -> float:
        """
        Calculate skill overlap percentage
        """
        set1 = set(s.lower() for s in skills1)
        set2 = set(s.lower() for s in skills2)
        
        if not set2:
            return 0.0
        
        overlap = len(set1 & set2)
        return overlap / len(set2)
    
    def find_missing(self, candidate_skills: List[str], required_skills: List[str]) -> List[str]:
        """
        Find skills candidate is missing
        """
        candidate_set = set(s.lower() for s in candidate_skills)
        required_set = set(s.lower() for s in required_skills)
        
        missing = required_set - candidate_set
        return sorted(list(missing))