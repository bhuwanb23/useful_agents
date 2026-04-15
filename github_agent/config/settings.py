# config/settings.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── GitHub ──────────────────────────
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_REPO = os.getenv("GITHUB_REPO")
    ISSUE_LABELS = os.getenv("ISSUE_LABELS", "bug,good-first-issue").split(",")
    MAX_ISSUES = int(os.getenv("MAX_ISSUES_PER_RUN", "5"))
    BASE_BRANCH = os.getenv("BASE_BRANCH", "main")
    
    # ── Ollama ──────────────────────────
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "codellama")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    
    # ── Notifications ───────────────────
    SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
    DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")
    
    # ── Agent Settings ──────────────────
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "50000"))  # bytes
    
    # ── Safety Settings ─────────────────
    PROTECTED_FILES = [
        '.env', '.github/workflows/', 'package-lock.json',
        'yarn.lock', 'Makefile', 'Dockerfile'
    ]
    PROTECTED_BRANCHES = ['main', 'master', 'production', 'develop']
    
    # ── Dashboard ───────────────────────
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5000"))
    DASHBOARD_SECRET = os.getenv("DASHBOARD_SECRET", "change-me-please")