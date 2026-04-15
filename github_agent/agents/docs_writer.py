# agents/docs_writer.py
# Automatically writes / updates documentation for fixed code

import re
import json
from typing import Dict, List, Optional
from core.base_agent import BaseAgent


class DocsWriterAgent(BaseAgent):
    """
    Reads code fixes and generates / updates:
      - Docstrings inside the code
      - README sections
      - CHANGELOG entry
      - Inline comments
    """

    def __init__(self):
        super().__init__(
            name="docs_writer",
            description="Writes and updates documentation for code changes"
        )
        self.capabilities = [
            "write_docs",
            "update_readme",
            "generate_docstrings",
            "write_changelog",
        ]

    # ──────────────────────────────────────────────────────────
    def can_handle(self, task: Dict) -> bool:
        return task.get("type") in ("write_docs", "update_docs")

    # ──────────────────────────────────────────────────────────
    async def execute(self, task: Dict) -> Dict:
        issue  = task.get("issue", {})
        fixes  = task.get("fixes", {})
        analysis = task.get("analysis", {})

        self.logger.info(f"📝 Writing docs for issue #{issue.get('number')}")

        docs_output: Dict[str, str] = {}

        # 1. Add / update docstrings inside each fixed file
        for file_path, file_data in fixes.items():
            updated = await self._add_docstrings(
                file_path,
                file_data.get("fixed", ""),
                issue,
            )
            if updated and updated != file_data.get("fixed"):
                docs_output[file_path] = updated

        # 2. Update README if it exists
        readme = await self._update_readme(issue, analysis, list(fixes.keys()))
        if readme:
            docs_output["README.md"] = readme

        # 3. Generate CHANGELOG entry
        changelog = await self._write_changelog_entry(issue, list(fixes.keys()))
        if changelog:
            existing = self.github.get_file_content("CHANGELOG.md")
            if existing:
                # Prepend new entry
                docs_output["CHANGELOG.md"] = changelog + "\n\n" + existing["content"]
            else:
                docs_output["CHANGELOG.md"] = changelog

        self.logger.info(
            f"✅ Docs generated for {len(docs_output)} files"
        )

        return {
            "issue":    issue,
            "fixes":    fixes,
            "docs":     docs_output,
            "analysis": analysis,
        }

    # ──────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ──────────────────────────────────────────────────────────

    async def _add_docstrings(
        self,
        file_path: str,
        code: str,
        issue: Dict,
    ) -> Optional[str]:
        """Ask Ollama to add / improve docstrings in the file."""

        ext = file_path.rsplit(".", 1)[-1] if "." in file_path else ""
        if ext not in ("py", "js", "ts", "java", "go", "rb"):
            return None          # Skip non-code files

        prompt = f"""Add or improve docstrings/comments in this code.

FILE: {file_path}
RECENT FIX CONTEXT: {issue.get('title', '')}

CODE:
{code[:4000]}

Rules:
- Add docstrings to every function / class that is missing one
- Keep existing docstrings, only improve them if they are wrong
- For Python use Google-style docstrings
- For JS/TS use JSDoc
- Return the COMPLETE file with docstrings added
- No markdown fences, no explanations"""

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a documentation expert. "
                    "Return only the complete file content with improved docs."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        result = self.ollama.chat(messages, temperature=0.2)
        return self._strip_markdown(result) if result else None

    # ──────────────────────────────────────────────────────────

    async def _update_readme(
        self,
        issue: Dict,
        analysis: Dict,
        changed_files: List[str],
    ) -> Optional[str]:
        """Update README if the issue mentions docs / readme."""

        labels = [l.lower() for l in issue.get("labels", [])]
        title  = issue.get("title", "").lower()

        needs_readme = any(
            kw in title or kw in " ".join(labels)
            for kw in ("readme", "doc", "documentation", "usage", "example")
        )

        if not needs_readme:
            return None

        readme_data = self.github.get_file_content("README.md")
        if not readme_data:
            return None

        prompt = f"""Update this README to reflect the recent fix.

ISSUE: {issue.get('title')}
DESCRIPTION: {issue.get('body', '')[:500]}
FILES CHANGED: {', '.join(changed_files)}

CURRENT README:
{readme_data['content'][:4000]}

Rules:
- Only update sections that are affected by the fix
- Keep all other content exactly the same
- Return the COMPLETE updated README
- No explanations, just the README content"""

        messages = [
            {
                "role": "system",
                "content": "You are a technical writer. Return only the README content.",
            },
            {"role": "user", "content": prompt},
        ]

        result = self.ollama.chat(messages, temperature=0.3)
        return result if result else None

    # ──────────────────────────────────────────────────────────

    async def _write_changelog_entry(
        self,
        issue: Dict,
        changed_files: List[str],
    ) -> Optional[str]:
        """Generate a CHANGELOG entry for this fix."""

        from datetime import date

        prompt = f"""Write a CHANGELOG entry for this fix.

DATE: {date.today().isoformat()}
ISSUE: #{issue.get('number')} - {issue.get('title')}
DESCRIPTION: {issue.get('body', '')[:300]}
FILES: {', '.join(changed_files)}

Format (Keep My Changelog style):
## [Unreleased]
### Fixed
- Brief description of what was fixed (#issue_number)

Return only the changelog block, nothing else."""

        messages = [
            {
                "role": "system",
                "content": "Write concise changelog entries in Keep a Changelog format.",
            },
            {"role": "user", "content": prompt},
        ]

        return self.ollama.chat(messages, temperature=0.2)

    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Remove markdown code fences from LLM output."""
        text = re.sub(r"```\w*\n?", "", text)
        text = re.sub(r"```",       "", text)
        return text.strip()