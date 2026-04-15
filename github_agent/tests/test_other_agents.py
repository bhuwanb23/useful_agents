# tests/test_other_agents.py
"""Tests for remaining agents: test_writer, pr_manager, docs_writer, dependency_agent"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock
from tests.conftest import make_agent

from agents.test_writer import TestWriterAgent
from agents.pr_manager import PRManagerAgent
from agents.docs_writer import DocsWriterAgent
from agents.dependency_agent import DependencyAgent


# ──────────────────────────────────────────────────────────────
# TEST WRITER AGENT
# ──────────────────────────────────────────────────────────────

class TestTestWriterAgent:

    def test_can_handle(self):
        """Test task type matching."""
        agent = make_agent(TestWriterAgent)
        assert agent.can_handle({"type": "write_tests"})
        assert not agent.can_handle({"type": "fix_code"})

    @pytest.mark.asyncio
    async def test_execute_generates_tests(self, sample_issue, sample_fixes):
        """Test that test writer generates test code."""
        agent = make_agent(TestWriterAgent)
        agent.ollama.chat = MagicMock(
            return_value=(
                "def test_divide():\n"
                "    assert divide(10, 2) == 5\n\n"
                "def test_divide_by_zero():\n"
                "    import pytest\n"
                "    with pytest.raises(ValueError):\n"
                "        divide(10, 0)\n"
            )
        )

        result = await agent.execute({
            "issue": sample_issue,
            "fixes": sample_fixes,
        })

        assert "tests" in result
        assert len(result["tests"]) > 0


# ──────────────────────────────────────────────────────────────
# PR MANAGER AGENT
# ──────────────────────────────────────────────────────────────

class TestPRManagerAgent:

    def test_can_handle(self):
        """Test task type matching."""
        agent = make_agent(PRManagerAgent)
        assert agent.can_handle({"type": "create_pr"})
        assert not agent.can_handle({"type": "fix_code"})

    @pytest.mark.asyncio
    async def test_execute_creates_pr(self, sample_issue, sample_fixes, sample_analysis):
        """Test PR creation workflow."""
        agent = make_agent(PRManagerAgent)
        
        # Mock GitHub operations
        agent.github.create_branch = MagicMock(return_value=True)
        agent.github.commit_file = MagicMock(return_value=True)
        
        mock_pr = MagicMock()
        mock_pr.number = 123
        mock_pr.html_url = "https://github.com/test/repo/pull/123"
        agent.github.create_pull_request = MagicMock(return_value=mock_pr)
        
        # Mock LLM for PR description
        agent.ollama.complete = MagicMock(
            return_value="## Summary\nFixed division by zero bug"
        )

        result = await agent.execute({
            "issue": sample_issue,
            "fixes": sample_fixes,
            "analysis": sample_analysis,
        })

        assert "pr" in result
        agent.github.create_branch.assert_called()
        agent.github.commit_file.assert_called()
        agent.github.create_pull_request.assert_called()


# ──────────────────────────────────────────────────────────────
# DOCS WRITER AGENT
# ──────────────────────────────────────────────────────────────

class TestDocsWriterAgent:

    def test_can_handle(self):
        """Test task type matching."""
        agent = make_agent(DocsWriterAgent)
        assert agent.can_handle({"type": "write_docs"})
        assert not agent.can_handle({"type": "fix_code"})

    @pytest.mark.asyncio
    async def test_execute_updates_docs(self, sample_issue, sample_fixes):
        """Test documentation generation."""
        agent = make_agent(DocsWriterAgent)
        
        agent.ollama.chat = MagicMock(
            return_value="## Changelog\n\n- Fixed division by zero issue"
        )
        agent.github.get_file_content = MagicMock(
            return_value={"content": "# README\n", "sha": "abc123"}
        )

        result = await agent.execute({
            "issue": sample_issue,
            "fixes": sample_fixes,
        })

        assert "docs" in result


# ──────────────────────────────────────────────────────────────
# DEPENDENCY AGENT
# ──────────────────────────────────────────────────────────────

class TestDependencyAgent:

    def test_can_handle(self):
        """Test task type matching."""
        agent = make_agent(DependencyAgent)
        assert agent.can_handle({"type": "check_deps"})
        assert not agent.can_handle({"type": "fix_code"})

    @pytest.mark.asyncio
    async def test_execute_checks_dependencies(self, sample_issue):
        """Test dependency checking."""
        agent = make_agent(DependencyAgent)
        
        # Mock to return a dependency file
        agent.github.get_repo_structure = MagicMock(
            return_value=["requirements.txt", "main.py"]
        )
        agent.github.get_file_content = MagicMock(
            return_value={
                "content": "requests==2.28.0\nflask==2.0.0\n",
                "sha": "abc123",
                "path": "requirements.txt"
            }
        )
        
        agent.ollama.chat = MagicMock(
            return_value=json.dumps({
                "issues": [],
                "safe_updates": []
            })
        )

        result = await agent.execute({
            "issue": sample_issue,
        })

        assert "dep_files" in result or "issues" in result
