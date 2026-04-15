# tests/test_integration.py
"""Integration tests for the complete workflow"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tests.conftest import make_agent

from agents.issue_analyzer import IssueAnalyzerAgent
from agents.code_fixer import CodeFixerAgent
from agents.code_reviewer import CodeReviewerAgent
from agents.security_scanner import SecurityScannerAgent
from agents.test_writer import TestWriterAgent
from agents.pr_manager import PRManagerAgent


# ──────────────────────────────────────────────────────────────
# FULL WORKFLOW TEST
# ──────────────────────────────────────────────────────────────

class TestFullWorkflow:
    """Test the complete issue-to-PR workflow."""

    @pytest.fixture
    def sample_issue(self):
        return {
            "number": 42,
            "title": "Fix division by zero in calculator",
            "body": "When the user inputs 0 as divisor the app crashes.",
            "labels": ["bug"],
            "comments": [],
            "url": "https://github.com/test/repo/issues/42",
        }

    @pytest.mark.asyncio
    async def test_issue_to_pr_workflow(self, sample_issue):
        """Test complete workflow from issue analysis to PR creation."""
        
        # 1. Issue Analyzer
        analyzer = make_agent(IssueAnalyzerAgent)
        analyzer.ollama.chat = MagicMock(
            return_value=(
                '{"summary":"Division by zero bug",'
                '"issue_type":"bug","complexity":"simple",'
                '"can_autofix":true,"confidence":90,'
                '"reason":"Simple validation fix",'
                '"files_to_modify":["calculator.py"],'
                '"approach":"Add zero check",'
                '"estimated_lines_changed":5,'
                '"risks":[],"requires_human_review":false}'
            )
        )
        analyzer.github.get_repo_structure = MagicMock(
            return_value=["calculator.py", "main.py"]
        )

        analysis_result = await analyzer.execute({"issue": sample_issue})
        assert analysis_result["analysis"]["can_autofix"] is True

        # 2. Code Fixer
        fixer = make_agent(CodeFixerAgent)
        fixer.github.get_repo_structure = MagicMock(
            return_value=["calculator.py"]
        )
        fixer.github.get_file_content = MagicMock(
            return_value={
                "content": "def divide(a, b):\n    return a / b\n",
                "sha": "abc123",
                "path": "calculator.py",
            }
        )
        fixer.ollama.chat = MagicMock(
            return_value=(
                "def divide(a, b):\n"
                "    # Fixed: check for zero divisor\n"
                "    if b == 0:\n"
                "        raise ValueError('Divisor cannot be zero')\n"
                "    return a / b\n"
            )
        )

        fix_result = await fixer.execute({
            "issue": sample_issue,
            "analysis": analysis_result["analysis"],
        })
        assert len(fix_result["fixes"]) > 0

        # 3. Code Reviewer
        reviewer = make_agent(CodeReviewerAgent)
        reviewer.ollama.chat = MagicMock(
            return_value=(
                '{"approved":true,"score":85,"fixes_the_issue":true,'
                '"introduces_bugs":false,"code_quality":"good",'
                '"security_concern":false,"style_consistent":true,'
                '"reason":"Looks good","suggestions":[]}'
            )
        )

        review_result = await reviewer.execute({
            "issue": sample_issue,
            "fixes": fix_result["fixes"],
            "analysis": analysis_result["analysis"],
        })
        assert review_result["approved"] is True

        # 4. Security Scanner
        scanner = make_agent(SecurityScannerAgent)
        scanner.ollama.chat = MagicMock(
            return_value=(
                '{"vulnerabilities":[],'
                '"overall_security":"good"}'
            )
        )

        security_result = await scanner.execute({
            "issue": sample_issue,
            "fixes": fix_result["fixes"],
        })
        assert security_result["has_critical"] is False
        assert security_result["scan_passed"] is True

        # 5. Test Writer
        test_writer = make_agent(TestWriterAgent)
        test_writer.ollama.chat = MagicMock(
            return_value=(
                "def test_divide_by_zero():\n"
                "    import pytest\n"
                "    with pytest.raises(ValueError):\n"
                "        divide(10, 0)\n"
            )
        )

        test_result = await test_writer.execute({
            "issue": sample_issue,
            "fixes": fix_result["fixes"],
        })
        assert "tests" in test_result

        # 6. PR Manager
        pr_manager = make_agent(PRManagerAgent)
        pr_manager.github.create_branch = MagicMock(return_value=True)
        pr_manager.github.commit_file = MagicMock(return_value=True)
        
        mock_pr = MagicMock()
        mock_pr.number = 123
        mock_pr.html_url = "https://github.com/test/repo/pull/123"
        pr_manager.github.create_pull_request = MagicMock(return_value=mock_pr)
        pr_manager.ollama.complete = MagicMock(
            return_value="## Summary\nFixed division by zero"
        )

        pr_result = await pr_manager.execute({
            "issue": sample_issue,
            "fixes": fix_result["fixes"],
            "tests": test_result["tests"],
            "analysis": analysis_result["analysis"],
        })
        
        assert "pr" in pr_result
        pr_manager.github.create_pull_request.assert_called()


# ──────────────────────────────────────────────────────────────
# WORKFLOW WITH REJECTIONS
# ──────────────────────────────────────────────────────────────

class TestWorkflowRejections:
    """Test workflow when issues are rejected at various stages."""

    @pytest.mark.asyncio
    async def test_workflow_blocked_by_security(self):
        """Test that security issues block PR creation."""
        from agents.security_scanner import SecurityScannerAgent
        
        scanner = make_agent(SecurityScannerAgent)
        scanner.ollama.chat = MagicMock(
            return_value=(
                '{"vulnerabilities":['
                '{"type":"sql_injection","severity":"critical",'
                '"line":5,"description":"SQL injection","fix":"Use params"}'
                '],"overall_security":"poor"}'
            )
        )

        result = await scanner.execute({
            "issue": {"number": 1, "title": "Test"},
            "fixes": {
                "db.py": {
                    "original": "",
                    "fixed": "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
                }
            },
        })

        assert result["has_critical"] is True
        assert result["scan_passed"] is False

    @pytest.mark.asyncio
    async def test_workflow_rejected_by_reviewer(self):
        """Test that poor code quality blocks progression."""
        from agents.code_reviewer import CodeReviewerAgent
        
        reviewer = make_agent(CodeReviewerAgent)
        reviewer.ollama.chat = MagicMock(
            return_value=(
                '{"approved":false,"score":30,"fixes_the_issue":false,'
                '"introduces_bugs":true,"code_quality":"poor",'
                '"security_concern":false,"style_consistent":false,'
                '"reason":"Introduces regression","suggestions":[]}'
            )
        )

        result = await reviewer.execute({
            "issue": {"number": 1, "title": "Test"},
            "fixes": {
                "calc.py": {
                    "original": "def add(a, b): return a + b",
                    "fixed": "def add(a, b): return a - b",  # Wrong fix!
                }
            },
            "analysis": {},
        })

        assert result["approved"] is False
        assert result["overall_score"] < 65


# ──────────────────────────────────────────────────────────────
# EDGE CASES
# ──────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_issue_body(self):
        """Test handling of issues with empty body."""
        analyzer = make_agent(IssueAnalyzerAgent)
        analyzer.ollama.chat = MagicMock(
            return_value=(
                '{"summary":"Empty issue",'
                '"issue_type":"documentation","complexity":"simple",'
                '"can_autofix":false,"confidence":50,'
                '"reason":"No details provided",'
                '"files_to_modify":[],'
                '"approach":"Need more info",'
                '"estimated_lines_changed":0,'
                '"risks":[],"requires_human_review":true}'
            )
        )
        analyzer.github.get_repo_structure = MagicMock(return_value=[])

        result = await analyzer.execute({
            "issue": {
                "number": 99,
                "title": "Something is wrong",
                "body": "",
                "labels": [],
            }
        })

        assert "analysis" in result
        assert result["analysis"]["can_autofix"] is False

    @pytest.mark.asyncio
    async def test_no_files_to_modify(self):
        """Test when no files are identified for fixing."""
        fixer = make_agent(CodeFixerAgent)
        fixer.github.get_repo_structure = MagicMock(return_value=[])
        fixer.ollama.chat = MagicMock(return_value="[]")  # No files suggested

        result = await fixer.execute({
            "issue": {"number": 1, "title": "Test"},
            "analysis": {"files_to_modify": [], "approach": "Fix it"},
        })

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_llm_returns_empty_response(self):
        """Test handling of empty LLM responses."""
        analyzer = make_agent(IssueAnalyzerAgent)
        analyzer.ollama.chat = MagicMock(return_value=None)
        analyzer.github.get_repo_structure = MagicMock(return_value=[])

        result = await analyzer.execute({
            "issue": {"number": 1, "title": "Test", "body": "Test", "labels": []}
        })

        # Should handle gracefully
        assert "error" in result or "analysis" in result

    @pytest.mark.asyncio
    async def test_binary_file_skipped(self):
        """Test that binary files are skipped during fixing."""
        fixer = make_agent(CodeFixerAgent)
        
        result = await fixer.execute({
            "issue": {"number": 1, "title": "Test"},
            "analysis": {
                "files_to_modify": ["image.png", "data.zip"],
                "approach": "Fix"
            },
        })

        # Should skip binary files
        assert result["success"] is False
