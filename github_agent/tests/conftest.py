# tests/conftest.py
# Shared fixtures and configuration for all tests

import os
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

# Add the github_agent root to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture
def sample_issue():
    """Sample GitHub issue for testing."""
    return {
        "number": 42,
        "title": "Fix division by zero in calculator",
        "body": "When the user inputs 0 as divisor the app crashes.",
        "labels": ["bug"],
        "comments": [],
        "url": "https://github.com/test/repo/issues/42",
        "author": "testuser",
        "created": "2024-01-01",
    }


@pytest.fixture
def sample_analysis():
    """Sample issue analysis result."""
    return {
        "summary": "Division by zero crash in calculator",
        "issue_type": "bug",
        "complexity": "simple",
        "can_autofix": True,
        "confidence": 90,
        "reason": "Simple input validation fix",
        "files_to_modify": ["calculator.py"],
        "approach": "Add a check for zero divisor and raise ValueError",
        "estimated_lines_changed": 5,
        "risks": [],
        "requires_human_review": False,
    }


@pytest.fixture
def sample_fixes():
    """Sample code fixes."""
    return {
        "calculator.py": {
            "original": "def divide(a, b):\n    return a / b\n",
            "fixed": (
                "def divide(a, b):\n"
                "    # Fixed: check for zero divisor\n"
                "    if b == 0:\n"
                "        raise ValueError('Divisor cannot be zero')\n"
                "    return a / b\n"
            ),
        }
    }


@pytest.fixture
def mock_memory():
    """Create a mock SharedMemory instance."""
    memory = AsyncMock()
    memory.set = AsyncMock()
    memory.get = AsyncMock(return_value=None)
    memory.delete = AsyncMock()
    memory.track_issue = AsyncMock()
    memory.update_issue = AsyncMock()
    memory.is_issue_processed = AsyncMock(return_value=False)
    memory.get_all_issues = AsyncMock(return_value=[])
    memory.log_action = AsyncMock()
    memory.get_agent_history = AsyncMock(return_value=[])
    return memory


@pytest.fixture
def mock_ollama():
    """Create a mock OllamaClient instance."""
    ollama = MagicMock()
    ollama.chat = MagicMock(return_value='{"status": "ok"}')
    ollama.complete = MagicMock(return_value="ok")
    ollama.json_complete = MagicMock(return_value={"status": "ok"})
    ollama.code_complete = MagicMock(return_value="code")
    ollama.list_models = MagicMock(return_value=["codellama"])
    ollama.is_healthy = MagicMock(return_value=True)
    return ollama


@pytest.fixture
def mock_github():
    """Create a mock GitHubClient instance."""
    github = MagicMock()
    github.get_open_issues = MagicMock(return_value=[])
    github.get_file_content = MagicMock(return_value=None)
    github.get_repo_structure = MagicMock(return_value=[])
    github.create_branch = MagicMock(return_value=True)
    github.branch_exists = MagicMock(return_value=False)
    github.delete_branch = MagicMock(return_value=True)
    github.commit_file = MagicMock(return_value=True)
    github.create_pull_request = MagicMock(return_value=None)
    github.get_pull_request = MagicMock(return_value=None)
    github.list_open_prs = MagicMock(return_value=[])
    github.add_issue_comment = MagicMock(return_value=True)
    github.add_label = MagicMock(return_value=True)
    github.get_default_branch = MagicMock(return_value="main")
    github.get_languages = MagicMock(return_value={"Python": 1000})
    return github


def make_agent(cls, mock_memory=None, mock_ollama=None, mock_github=None):
    """Create an agent with mocked dependencies."""
    agent = cls()
    agent.memory = mock_memory or AsyncMock()
    agent.ollama = mock_ollama or MagicMock()
    agent.github = mock_github or MagicMock()
    return agent
