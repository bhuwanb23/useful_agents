# tools/file_manager.py
# High-level file operations used by multiple agents

import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class FileManager:
    """
    Helpers for working with repo files:
      - Language detection
      - Safety checks (don't touch protected files)
      - Ranking files by relevance to an issue
    """

    BINARY_EXTENSIONS: Set[str] = {
        "png", "jpg", "jpeg", "gif", "svg", "ico", "bmp",
        "pdf", "zip", "tar", "gz", "rar",
        "exe", "dll", "so", "dylib",
        "pyc", "pyo", "class",
        "mp3", "mp4", "wav", "avi",
        "ttf", "woff", "woff2", "eot",
        "sqlite", "db",
    }

    TEXT_EXTENSIONS: Set[str] = {
        "py", "js", "ts", "jsx", "tsx",
        "java", "go", "rs", "rb", "php",
        "c", "cpp", "h", "hpp", "cs",
        "html", "css", "scss", "less",
        "json", "yaml", "yml", "toml", "ini", "cfg",
        "md", "rst", "txt",
        "sh", "bash", "zsh",
        "sql",
        "dockerfile", "makefile",
        "xml", "csv",
    }

    PROTECTED_PATHS: Set[str] = {
        ".env", ".env.local", ".env.production",
        ".github/workflows",
        "package-lock.json", "yarn.lock", "Pipfile.lock",
        "Makefile",
        "Dockerfile",
        ".gitignore", ".gitattributes",
    }

    def __init__(self):
        self.logger = logging.getLogger("tools.file_manager")

    # ──────────────────────────────────────────────────────────

    def get_extension(self, file_path: str) -> str:
        """Return lowercase file extension without the dot."""
        return Path(file_path).suffix.lstrip(".").lower()

    def get_language(self, file_path: str) -> str:
        """Map file extension to human-readable language name."""
        ext_map = {
            "py":   "Python",  "js":   "JavaScript",
            "ts":   "TypeScript", "jsx":  "JavaScript",
            "tsx":  "TypeScript", "java": "Java",
            "go":   "Go",      "rs":   "Rust",
            "rb":   "Ruby",    "php":  "PHP",
            "c":    "C",       "cpp":  "C++",
            "cs":   "C#",      "html": "HTML",
            "css":  "CSS",     "scss": "SCSS",
            "sh":   "Shell",   "md":   "Markdown",
            "sql":  "SQL",     "yaml": "YAML",
            "yml":  "YAML",    "json": "JSON",
            "toml": "TOML",    "rs":   "Rust",
        }
        ext = self.get_extension(file_path)
        return ext_map.get(ext, "Unknown")

    # ──────────────────────────────────────────────────────────

    def is_binary(self, file_path: str) -> bool:
        """Return True if the file is likely binary."""
        return self.get_extension(file_path) in self.BINARY_EXTENSIONS

    def is_text(self, file_path: str) -> bool:
        """Return True if the file is likely plain text / code."""
        ext = self.get_extension(file_path)
        name = Path(file_path).name.lower()
        return (
            ext in self.TEXT_EXTENSIONS
            or name in ("dockerfile", "makefile", "gemfile", "procfile")
        )

    def is_protected(self, file_path: str) -> bool:
        """
        Return True if the file should NEVER be auto-modified.
        """
        path_lower = file_path.lower()
        for protected in self.PROTECTED_PATHS:
            if protected in path_lower:
                return True
        return False

    # ──────────────────────────────────────────────────────────

    def rank_by_relevance(
        self,
        file_paths:   List[str],
        issue_title:  str,
        issue_body:   str,
        analysis:     Optional[Dict] = None,
    ) -> List[Tuple[str, float]]:
        """
        Score each file by how relevant it is to the issue.

        Returns list of (file_path, score) sorted descending.
        """
        keywords = self._extract_keywords(issue_title + " " + issue_body)
        suggested = set(
            (analysis or {}).get("files_to_modify", [])
        )

        scored: List[Tuple[str, float]] = []

        for fp in file_paths:
            if self.is_binary(fp) or self.is_protected(fp):
                continue

            score = 0.0

            # Suggested by LLM analysis — highest weight
            if fp in suggested or any(s in fp for s in suggested):
                score += 10.0

            # Keyword match in file path
            fp_lower = fp.lower()
            for kw in keywords:
                if len(kw) > 3 and kw in fp_lower:
                    score += 2.0

            # Prefer source files over config / lock files
            ext = self.get_extension(fp)
            if ext in ("py", "js", "ts", "java", "go", "rb"):
                score += 1.0
            elif ext in ("json", "yaml", "toml", "lock"):
                score -= 1.0

            # Penalise test files slightly (fixer agent handles source)
            if "test" in fp_lower or "spec" in fp_lower:
                score -= 0.5

            scored.append((fp, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # ──────────────────────────────────────────────────────────

    def filter_for_context(
        self,
        file_paths: List[str],
        issue_title: str,
        issue_body:  str,
        max_files:   int = 10,
    ) -> List[str]:
        """
        Return the top N most relevant, non-binary, non-protected files.
        """
        ranked = self.rank_by_relevance(file_paths, issue_title, issue_body)
        return [fp for fp, _ in ranked[:max_files]]

    # ──────────────────────────────────────────────────────────
    # INTERNAL
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extract meaningful words from issue text."""
        # Remove 
        words = re.findall(r"[a-zA-Z_]\w+", text.lower())

        stop_words = {
            "the", "and", "for", "with", "this", "that", "from",
            "when", "have", "not", "are", "but", "its", "also",
            "issue", "problem", "error", "bug", "fix", "should",
            "would", "could", "does", "will", "can", "get",
        }

        return [w for w in words if w not in stop_words and len(w) > 2]