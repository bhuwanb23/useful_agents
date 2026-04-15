import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # GitHub Settings
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_REPO = os.getenv("GITHUB_REPO")          # "owner/repo"
    
    # Ollama Settings
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "codellama")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Agent Settings
    MAX_ISSUES = int(os.getenv("MAX_ISSUES_PER_RUN", 5))
    ISSUE_LABELS = os.getenv("ISSUE_LABELS", "bug").split(",")
    
    # Branch naming
    BRANCH_PREFIX = "auto-fix"