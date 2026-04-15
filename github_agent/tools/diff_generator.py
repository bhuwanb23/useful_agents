# tools/diff_generator.py
# Generates human-readable diffs between original and fixed code

import difflib
import logging
from typing import Dict, List, Optional, Tuple


class DiffGenerator:
    """
    Generates and parses diffs between original and fixed code.

    Outputs:
      - Unified diff (standard patch format)
      - HTML diff (for dashboard display)
      - Summary stats (lines added/removed)
    """

    def __init__(self):
        self.logger = logging.getLogger("tools.diff_generator")

    # ──────────────────────────────────────────────────────────

    def unified_diff(
        self,
        original:  str,
        fixed:     str,
        file_path: str = "file",
        context:   int = 3,
    ) -> str:
        """
        Standard unified diff (like `git diff`).

        Returns a string you can save as a .patch file.
        """
        original_lines = original.splitlines(keepends=True)
        fixed_lines    = fixed.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            n=context,
        )

        return "".join(diff)

    # ──────────────────────────────────────────────────────────

    def html_diff(
        self,
        original:  str,
        fixed:     str,
        file_path: str = "file",
    ) -> str:
        """
        Side-by-side HTML diff for the dashboard.
        """
        original_lines = original.splitlines()
        fixed_lines    = fixed.splitlines()

        differ = difflib.HtmlDiff(wrapcolumn=80)
        return differ.make_file(
            original_lines,
            fixed_lines,
            fromdesc=f"Original: {file_path}",
            todesc=f"Fixed: {file_path}",
            context=True,
            numlines=3,
        )

    # ──────────────────────────────────────────────────────────

    def stats(self, original: str, fixed: str) -> Dict:
        """
        Calculate change statistics.

        Returns:
            {
                "lines_added":   int,
                "lines_removed": int,
                "lines_changed": int,
                "changed_pct":   float,   # percentage of file changed
            }
        """
        original_lines = original.splitlines()
        fixed_lines    = fixed.splitlines()

        matcher = difflib.SequenceMatcher(None, original_lines, fixed_lines)

        added   = 0
        removed = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "insert":
                added   += j2 - j1
            elif tag == "delete":
                removed += i2 - i1
            elif tag == "replace":
                added   += j2 - j1
                removed += i2 - i1

        total = max(len(original_lines), 1)

        return {
            "lines_added":   added,
            "lines_removed": removed,
            "lines_changed": added + removed,
            "changed_pct":   round((added + removed) / total * 100, 1),
            "original_lines": len(original_lines),
            "fixed_lines":    len(fixed_lines),
        }

    # ──────────────────────────────────────────────────────────

    def changed_sections(
        self,
        original: str,
        fixed:    str,
    ) -> List[Dict]:
        """
        Return a list of changed blocks with surrounding context.
        Useful for building clear PR descriptions.

        Each block: {"type": "added|removed|replaced", "lines": [...]}
        """
        original_lines = original.splitlines()
        fixed_lines    = fixed.splitlines()

        matcher = difflib.SequenceMatcher(None, original_lines, fixed_lines)
        sections = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue

            sections.append({
                "type":          tag,
                "original_lines": original_lines[i1:i2],
                "fixed_lines":    fixed_lines[j1:j2],
                "start_line":    i1 + 1,
            })

        return sections

    # ──────────────────────────────────────────────────────────

    def format_for_pr(
        self,
        fixes: Dict[str, Dict],
        max_lines: int = 50,
    ) -> str:
        """
        Build a markdown diff summary for PR descriptions.

        Args:
            fixes: {file_path: {"original": str, "fixed": str}}
            max_lines: max diff lines to include per file
        """
        parts = []

        for file_path, data in fixes.items():
            original = data.get("original", "")
            fixed    = data.get("fixed",    "")

            stats = self.stats(original, fixed)
            diff  = self.unified_diff(original, fixed, file_path)

            # Trim long diffs
            diff_lines = diff.splitlines()
            if len(diff_lines) > max_lines:
                diff_lines = diff_lines[:max_lines]
                diff_lines.append(f"... ({len(diff_lines)} more lines)")
            diff_trimmed = "\n".join(diff_lines)

            parts.append(
                f"### `{file_path}`\n"
                f"**+{stats['lines_added']} / -{stats['lines_removed']} lines "
                f"({stats['changed_pct']}% changed)**\n\n"
                f"```diff\n{diff_trimmed}\n```"
            )

        return "\n\n".join(parts)