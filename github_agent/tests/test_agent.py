# tests/test_agent.py

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.issue_analyzer   import IssueAnalyzerAgent
from agents.code_fixer       import CodeFixerAgent
from agents.code_reviewer    import CodeReviewerAgent
from agents.security_scanner import SecurityScannerAgent
from agents.test_writer      import TestWriterAgent
from tests.conftest import make_agent


# ──────────────────────────────────────────────────────────────
# FIXTURES
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_issue():
    return {
        "number":   42,
        "title":    "Fix division by zero in calculator",
        "body":     "When the user inputs 0 as divisor the app crashes.",
        "labels":   ["bug"],
        "comments": [],
        "url":      "https://github.com/test/repo/issues/42",
    }


@pytest.fixture
def sample_analysis():
    return {
        "summary":           "Division by zero crash in calculator",
        "issue_type":        "bug",
        "complexity":        "simple",
        "can_autofix":       True,
        "confidence":        90,
        "reason":            "Simple input validation fix",
        "files_to_modify":   ["calculator.py"],
        "approach":          "Add a check for zero divisor and raise ValueError",
        "estimated_lines_changed": 5,
        "risks":             [],
        "requires_human_review": False,
    }


@pytest.fixture
def sample_fixes():
    return {
        "calculator.py": {
            "original": "def divide(a, b):\n    return a / b\n",
            "fixed":    (
                "def divide(a, b):\n"
                "    # Fixed: check for zero divisor\n"
                "    if b == 0:\n"
                "        raise ValueError('Divisor cannot be zero')\n"
                "    return a / b\n"
            ),
        }
    }



# ──────────────────────────────────────────────────────────────
# ISSUE ANALYZER
# ──────────────────────────────────────────────────────────────

class TestIssueAnalyzerAgent:

    def test_can_handle(self, sample_issue):
        agent = make_agent(IssueAnalyzerAgent)
        assert agent.can_handle({"type": "analyze_issue"})
        assert not agent.can_handle({"type": "fix_code"})

    @pytest.mark.asyncio
    async def test_execute_success(self, sample_issue, sample_analysis):
        agent = make_agent(IssueAnalyzerAgent)

        # Mock Ollama returning valid JSON
        agent.ollama.chat.return_value = (
            '{"summary":"test","issue_type":"bug","complexity":"simple",'
            '"can_autofix":true,"confidence":90,"reason":"ok",'
            '"files_to_modify":["calculator.py"],'
            '"approach":"add check","estimated_lines_changed":5,'
            '"risks":[],"requires_human_review":false}'
        )
        agent.github.get_repo_structure.return_value = ["calculator.py"]

        result = await agent.execute({"issue": sample_issue})

        assert "analysis" in result
        assert result["analysis"]["can_autofix"] is True
        agent.memory.set.assert_called()
        agent.memory.update_issue.assert_called()

    @pytest.mark.asyncio
    async def test_execute_bad_llm_response(self, sample_issue):
        agent = make_agent(IssueAnalyzerAgent)
        agent.ollama.chat.return_value = "not json at all"
        agent.github.get_repo_structure.return_value = []

        result = await agent.execute({"issue": sample_issue})

        # Should handle gracefully
        assert "analysis" in result or "error" in result


# ──────────────────────────────────────────────────────────────
# CODE FIXER
# ──────────────────────────────────────────────────────────────

class TestCodeFixerAgent:

    def test_can_handle(self):
        agent = make_agent(CodeFixerAgent)
        assert agent.can_handle({"type": "fix_code"})

    @pytest.mark.asyncio
    async def test_fix_generates_output(self, sample_issue, sample_analysis, sample_fixes):
        agent = make_agent(CodeFixerAgent)

        # Setup mocks
        agent.github.get_repo_structure.return_value = ["calculator.py"]
        agent.github.get_file_content.return_value = {
            "content": sample_fixes["calculator.py"]["original"],
            "sha":     "abc123",
            "path":    "calculator.py",
        }
        agent.ollama.chat.return_value = sample_fixes["calculator.py"]["fixed"]

        result = await agent.execute({
            "issue":    sample_issue,
            "analysis": sample_analysis,
        })

        assert "fixes" in result
        assert len(result["fixes"]) > 0

    @pytest.mark.asyncio
    async def test_no_fix_when_content_unchanged(self, sample_issue, sample_analysis):
        agent = make_agent(CodeFixerAgent)

        original = "def divide(a, b):\n    return a / b\n"
        agent.github.get_repo_structure.return_value = ["calculator.py"]
        agent.github.get_file_content.return_value = {
            "content": original, "sha": "abc", "path": "calculator.py"
        }
        # LLM returns same content
        agent.ollama.chat.return_value = original

        result = await agent.execute({
            "issue":    sample_issue,
            "analysis": sample_analysis,
        })

        # Should not produce fixes if nothing changed
        fixes = result.get("fixes", {})
        assert len(fixes) == 0 or all(
            v.get("fixed") != v.get("original") for v in fixes.values()
        )


# ──────────────────────────────────────────────────────────────
# CODE REVIEWER
# ──────────────────────────────────────────────────────────────

class TestCodeReviewerAgent:

    def test_can_handle(self):
        agent = make_agent(CodeReviewerAgent)
        assert agent.can_handle({"type": "review_code"})

    @pytest.mark.asyncio
    async def test_approve_good_fix(self, sample_issue, sample_fixes, sample_analysis):
        agent = make_agent(CodeReviewerAgent)
        agent.ollama.chat.return_value = (
            '{"approved":true,"score":85,"fixes_the_issue":true,'
            '"introduces_bugs":false,"code_quality":"good",'
            '"security_concern":false,"style_consistent":true,'
            '"reason":"looks good","suggestions":[]}'
        )

        result = await agent.execute({
            "issue":    sample_issue,
            "fixes":    sample_fixes,
            "analysis": sample_analysis,
        })

        assert result["approved"] is True
        assert result["overall_score"] >= 65

    @pytest.mark.asyncio
    async def test_reject_bad_fix(self, sample_issue, sample_fixes, sample_analysis):
        agent = make_agent(CodeReviewerAgent)
        agent.ollama.chat.return_value = (
            '{"approved":false,"score":30,"fixes_the_issue":false,'
            '"introduces_bugs":true,"code_quality":"poor",'
            '"security_concern":false,"style_consistent":false,'
            '"reason":"introduces a regression","suggestions":[]}'
        )

        result = await agent.execute({
            "issue":    sample_issue,
            "fixes":    sample_fixes,
            "analysis": sample_analysis,
        })

        assert result["approved"] is False


# ──────────────────────────────────────────────────────────────
# SECURITY SCANNER
# ──────────────────────────────────────────────────────────────

class TestSecurityScannerAgent:

    def test_can_handle(self):
        agent = make_agent(SecurityScannerAgent)
        assert agent.can_handle({"type": "scan_security"})

    def test_pattern_scan_detects_sql_injection(self):
        agent = make_agent(SecurityScannerAgent)
        bad_code = "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')"
        vulns = agent._pattern_scan(bad_code, "db.py")
        assert len(vulns) > 0

    def test_pattern_scan_clean_code(self):
        agent = make_agent(SecurityScannerAgent)
        clean_code = (
            "def divide(a, b):\n"
            "    if b == 0:\n"
            "        raise ValueError('zero')\n"
            "    return a / b\n"
        )
        vulns = agent._pattern_scan(clean_code, "calc.py")
        assert len(vulns) == 0

    @pytest.mark.asyncio
    async def test_critical_blocks_pr(self, sample_issue):
        agent = make_agent(SecurityScannerAgent)
        agent.ollama.chat.return_value = (
            '{"vulnerabilities":[{"type":"sql_injection",'
            '"severity":"critical","line":5,"description":"raw sql",'
            '"fix":"use parameterized queries"}],"overall_security":"poor"}'
        )

        result = await agent.execute({
            "issue": sample_issue,
            "fixes": {
                "db.py": {
                    "original": "",
                    "fixed":    "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
                }
            },
        })

        assert result["has_critical"] is True
        assert result["scan_passed"] is False