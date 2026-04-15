# tests/test_clients.py

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from clients.ollama_client import OllamaClient
from tools.validator       import Validator
from tools.diff_generator  import DiffGenerator
from tools.code_parser     import CodeParser
from tools.file_manager    import FileManager


# ──────────────────────────────────────────────────────────────
# OLLAMA CLIENT
# ──────────────────────────────────────────────────────────────

class TestOllamaClient:

    @patch("clients.ollama_client.requests.get")
    @patch("clients.ollama_client.requests.post")
    def test_chat_returns_content(self, mock_post, mock_get):
        # Mock /api/tags
        mock_get.return_value.json.return_value = {
            "models": [{"name": "codellama"}]
        }
        # Mock /api/chat
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "message": {"content": "Hello, world!"}
        }

        client = OllamaClient()
        result = client.chat([{"role": "user", "content": "hi"}])

        assert result == "Hello, world!"

    @patch("clients.ollama_client.requests.get")
    @patch("clients.ollama_client.requests.post")
    def test_json_complete_parses_json(self, mock_post, mock_get):
        mock_get.return_value.json.return_value = {"models": [{"name": "codellama"}]}
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "message": {"content": '{"key": "value"}'}
        }

        client = OllamaClient()
        result = client.json_complete("return json")

        assert result == {"key": "value"}

    @patch("clients.ollama_client.requests.get")
    @patch("clients.ollama_client.requests.post")
    def test_chat_retries_on_timeout(self, mock_post, mock_get):
        import requests as req_lib
        mock_get.return_value.json.return_value = {"models": [{"name": "codellama"}]}

        # First two calls time out, third succeeds
        mock_post.side_effect = [
            req_lib.exceptions.Timeout,
            req_lib.exceptions.Timeout,
            MagicMock(
                status_code=200,
                json=lambda: {"message": {"content": "ok"}},
                raise_for_status=lambda: None,
            ),
        ]

        client = OllamaClient()
        result = client.chat([{"role": "user", "content": "hi"}], retries=3)
        assert result == "ok"


# ──────────────────────────────────────────────────────────────
# VALIDATOR
# ──────────────────────────────────────────────────────────────

class TestValidator:

    def setup_method(self):
        self.v = Validator()

    # Size checks
    def test_size_ok(self):
        ok, _ = self.v.check_size("a" * 100, "a" * 120)
        assert ok

    def test_size_too_large(self):
        ok, msg = self.v.check_size("a" * 100, "a" * 400)
        assert not ok
        assert "size" in msg.lower()

    def test_size_too_small(self):
        ok, msg = self.v.check_size("a" * 1000, "a" * 10)
        assert not ok

    # Syntax checks
    def test_python_syntax_ok(self):
        ok, _ = self.v.check_syntax("def foo():\n    return 1\n", "f.py")
        assert ok

    def test_python_syntax_bad(self):
        ok, msg = self.v.check_syntax("def foo(:\n    return 1\n", "f.py")
        assert not ok
        assert "SyntaxError" in msg

    def test_json_syntax_ok(self):
        ok, _ = self.v.check_syntax('{"a": 1}', "f.json")
        assert ok

    def test_json_syntax_bad(self):
        ok, _ = self.v.check_syntax("{bad json}", "f.json")
        assert not ok

    # Dangerous patterns
    def test_safe_code_passes(self):
        safe, _ = self.v.check_dangerous_patterns("def add(a, b): return a + b")
        assert safe

    def test_rm_rf_blocked(self):
        safe, matches = self.v.check_dangerous_patterns("os.system('rm -rf /')")
        assert not safe

    # Full validation
    def test_validate_fix_passes(self):
        original = "def divide(a, b):\n    return a / b\n"
        fixed    = (
            "def divide(a, b):\n"
            "    if b == 0:\n"
            "        raise ValueError('zero')\n"
            "    return a / b\n"
        )
        result = self.v.validate_fix(original, fixed, "calc.py")
        assert result["valid"] is True

    def test_validate_fix_fails_syntax(self):
        result = self.v.validate_fix("x = 1\n", "def foo(:\n    pass\n", "f.py")
        assert result["valid"] is False
        assert any("syntax" in e.lower() for e in result["errors"])


# ──────────────────────────────────────────────────────────────
# DIFF GENERATOR
# ──────────────────────────────────────────────────────────────

class TestDiffGenerator:

    def setup_method(self):
        self.dg = DiffGenerator()

    def test_unified_diff_detects_change(self):
        diff = self.dg.unified_diff("a = 1\n", "a = 2\n", "f.py")
        assert "-a = 1" in diff
        assert "+a = 2" in diff

    def test_stats_additions(self):
        stats = self.dg.stats("line1\n", "line1\nline2\n")
        assert stats["lines_added"] == 1

    def test_stats_deletions(self):
        stats = self.dg.stats("line1\nline2\n", "line1\n")
        assert stats["lines_removed"] == 1

    def test_no_diff_identical(self):
        diff = self.dg.unified_diff("same\n", "same\n")
        assert diff == ""

    def test_changed_sections(self):
        sections = self.dg.changed_sections("a\nb\nc\n", "a\nX\nc\n")
        assert len(sections) >= 1


# ──────────────────────────────────────────────────────────────
# CODE PARSER
# ──────────────────────────────────────────────────────────────

class TestCodeParser:

    def setup_method(self):
        self.cp = CodeParser()

    def test_parse_python_functions(self):
        code = (
            "def add(a, b):\n"
            "    return a + b\n\n"
            "async def fetch(url):\n"
            "    pass\n"
        )
        result = self.cp.parse(code, "math.py")
        names = [f["name"] for f in result["functions"]]
        assert "add" in names
        assert "fetch" in names

    def test_parse_python_class(self):
        code = "class Calculator:\n    def add(self, a, b):\n        return a + b\n"
        result = self.cp.parse(code, "calc.py")
        assert any(c["name"] == "Calculator" for c in result["classes"])

    def test_parse_python_imports(self):
        code = "import os\nfrom pathlib import Path\n"
        result = self.cp.parse(code, "f.py")
        assert "os" in result["imports"]
        assert "pathlib.Path" in result["imports"]

    def test_extract_todos(self):
        code = "x = 1  # TODO: fix this later\n# FIXME: broken\n"
        todos = self.cp._extract_todos(code)
        assert any(t["type"] == "TODO" for t in todos)
        assert any(t["type"] == "FIXME" for t in todos)

    def test_syntax_error_captured(self):
        code = "def foo(:\n    pass\n"
        result = self.cp.parse(code, "bad.py")
        assert len(result["errors"]) > 0

    def test_summarize(self):
        code = "class Foo:\n    def bar(self): pass\n"
        summary = self.cp.summarize(code, "foo.py")
        assert "Foo" in summary or "bar" in summary


# ──────────────────────────────────────────────────────────────
# FILE MANAGER
# ──────────────────────────────────────────────────────────────

class TestFileManager:

    def setup_method(self):
        self.fm = FileManager()

    def test_is_binary(self):
        assert self.fm.is_binary("image.png")
        assert self.fm.is_binary("archive.zip")
        assert not self.fm.is_binary("code.py")

    def test_is_text(self):
        assert self.fm.is_text("main.py")
        assert self.fm.is_text("index.js")
        assert not self.fm.is_text("photo.jpg")

    def test_is_protected(self):
        assert self.fm.is_protected(".env")
        assert self.fm.is_protected(".github/workflows/ci.yml")
        assert not self.fm.is_protected("src/main.py")

    def test_get_language(self):
        assert self.fm.get_language("main.py")    == "Python"
        assert self.fm.get_language("app.js")     == "JavaScript"
        assert self.fm.get_language("index.ts")   == "TypeScript"
        assert self.fm.get_language("README.md")  == "Markdown"

    def test_rank_by_relevance(self):
        files = [
            "src/calculator.py",
            "tests/test_calc.py",
            "README.md",
            "package-lock.json",
        ]
        ranked = self.fm.rank_by_relevance(
            files,
            "Fix division by zero in calculator",
            "The calculator crashes when dividing by zero",
        )
        # calculator.py should rank highest
        top_file = ranked[0][0] if ranked else ""
        assert "calculator" in top_file