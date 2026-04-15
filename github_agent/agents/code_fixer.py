# agents/code_fixer.py

import json
import re
import ast
from typing import Dict, List, Optional
from core.base_agent import BaseAgent


class CodeFixerAgent(BaseAgent):
    """
    The main coding agent.
    - Reads relevant files from the repo
    - Generates fixes using the local Ollama LLM
    - Validates output before returning
    """

    def __init__(self):
        super().__init__(
            name="code_fixer",
            description="Generates code fixes for GitHub issues"
        )
        self.capabilities = ["fix_code", "generate_code", "modify_files"]

        # File extensions we know how to validate
        self.VALIDATABLE_EXTENSIONS = {"py", "json"}

        # Extensions we treat as pure text / config
        self.TEXT_EXTENSIONS = {
            "md", "txt", "rst", "yaml", "yml",
            "toml", "cfg", "ini", "sh", "bash"
        }

        # Extensions we skip entirely (binary / generated)
        self.SKIP_EXTENSIONS = {
            "png", "jpg", "jpeg", "gif", "svg", "ico",
            "pdf", "zip", "tar", "gz",
            "pyc", "pyo", "class",
            "lock", "sum",
        }

    # ------------------------------------------------------------------
    # INTERFACE
    # ------------------------------------------------------------------

    def can_handle(self, task: Dict) -> bool:
        return task.get("type") == "fix_code"

    # ------------------------------------------------------------------
    # MAIN EXECUTION
    # ------------------------------------------------------------------

    async def execute(self, task: Dict) -> Dict:
        issue    = task.get("issue", {})
        analysis = task.get("analysis", {})

        self.logger.info(f"Fixing issue #{issue.get('number')}: {issue.get('title')}")

        # ── 1. Decide which files to touch ────────────────────────────
        files_to_modify: List[str] = analysis.get("files_to_modify", [])

        if not files_to_modify:
            self.logger.info("No files suggested by analysis — asking LLM")
            files_to_modify = await self._find_relevant_files(issue, analysis)

        if not files_to_modify:
            self.logger.warning("Could not identify any files to modify")
            return {
                "success":      False,
                "error":        "Could not identify files to modify",
                "issue":        issue,
                "analysis":     analysis,
                "fixes":        {},
                "files_changed": [],
            }

        self.logger.info(f"Files to modify: {files_to_modify}")

        # ── 2. Generate a fix for each file ───────────────────────────
        fixes: Dict[str, Dict] = {}

        for file_path in files_to_modify[:5]:       # hard cap at 5 files
            ext = self._get_extension(file_path)

            if ext in self.SKIP_EXTENSIONS:
                self.logger.info(f"Skipping binary/generated file: {file_path}")
                continue

            self.logger.info(f"Generating fix for: {file_path}")
            fix = await self._fix_file(issue, analysis, file_path)

            if fix:
                fixes[file_path] = fix
                self.logger.info(f"Fix ready for: {file_path}")
            else:
                self.logger.warning(f"No fix produced for: {file_path}")

        # ── 3. Nothing worked ─────────────────────────────────────────
        if not fixes:
            return {
                "success":       False,
                "error":         "No fixes could be generated for any file",
                "issue":         issue,
                "analysis":      analysis,
                "fixes":         {},
                "files_changed": [],
            }

        # ── 4. Persist to shared memory ───────────────────────────────
        await self.memory.set(
            f"issue.{issue['number']}.fixes",
            {
                k: {"original_snippet": v["original"][:300], "path": k}
                for k, v in fixes.items()
            },
        )

        await self.memory.update_issue(
            issue["number"],
            status="fixed",
            fixes=json.dumps(list(fixes.keys())),
        )

        self.logger.info(f"Generated fixes for {len(fixes)} file(s)")

        return {
            "success":       True,
            "issue":         issue,
            "analysis":      analysis,
            "fixes":         fixes,
            "files_changed": list(fixes.keys()),
        }

    # ------------------------------------------------------------------
    # FILE DISCOVERY
    # ------------------------------------------------------------------

    async def _find_relevant_files(
        self,
        issue:    Dict,
        analysis: Dict,
    ) -> List[str]:
        """
        Ask the LLM which files in the repo are relevant to the issue.
        Falls back to keyword matching if the LLM gives a bad response.
        """
        repo_files = self.github.get_repo_structure()

        if not repo_files:
            return []

        # Build a compact file listing (skip binaries)
        listing = [
            f for f in repo_files
            if self._get_extension(f) not in self.SKIP_EXTENSIONS
        ]

        file_list_text = "\n".join(listing[:200])   # keep prompt manageable

        prompt = (
            "You are a senior software engineer.\n"
            "Given the GitHub issue below and the list of files in the repository, "
            "return ONLY a JSON array of file paths that need to be modified to fix "
            "the issue. Return at most 5 files. If you are unsure, return an empty "
            "array.\n\n"
            f"ISSUE TITLE: {issue.get('title', '')}\n"
            f"ISSUE BODY:\n{issue.get('body', '')[:600]}\n\n"
            f"SUGGESTED APPROACH: {analysis.get('approach', '')}\n\n"
            f"REPOSITORY FILES:\n{file_list_text}\n\n"
            'Respond with a JSON array only, for example: ["src/app.py", "utils/helper.py"]'
        )

        messages = [
            {
                "role":    "system",
                "content": (
                    "You are a code navigation expert. "
                    "Respond with a JSON array of file paths only. "
                    "No explanation, no markdown, no prose."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response = self.ollama.chat(messages, temperature=0.1)

        if not response:
            return self._keyword_fallback(issue, listing)

        # Try to extract a JSON array from the response
        suggested = self._parse_file_list(response)

        if not suggested:
            self.logger.warning("LLM returned no valid file list — using keyword fallback")
            return self._keyword_fallback(issue, listing)

        # Only keep files that actually exist in the repo
        valid = [f for f in suggested if f in repo_files]

        self.logger.info(f"LLM suggested {len(suggested)} file(s), {len(valid)} exist in repo")
        return valid

    def _parse_file_list(self, text: str) -> List[str]:
        """Extract a JSON array of strings from arbitrary LLM output."""
        # Try direct parse first
        text = text.strip()
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return [str(x) for x in result]
        except json.JSONDecodeError:
            pass

        # Look for the first [...] block
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                if isinstance(result, list):
                    return [str(x) for x in result]
            except json.JSONDecodeError:
                pass

        return []

    def _keyword_fallback(self, issue: Dict, repo_files: List[str]) -> List[str]:
        """
        Simple keyword matching when the LLM cannot identify files.
        Scores each file by how many issue words appear in its path.
        """
        title = issue.get("title", "")
        body  = issue.get("body",  "")

        # Pull out meaningful words (length > 3, not stop-words)
        stop = {
            "this", "that", "with", "from", "have", "when",
            "will", "should", "issue", "error", "problem",
            "please", "hello", "about",
        }
        words = [
            w.lower() for w in re.findall(r"[a-zA-Z_]\w+", title + " " + body)
            if len(w) > 3 and w.lower() not in stop
        ]

        scored = []
        for fp in repo_files:
            fp_lower = fp.lower()
            score = sum(1 for w in words if w in fp_lower)
            if score > 0:
                scored.append((fp, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [fp for fp, _ in scored[:5]]

    # ------------------------------------------------------------------
    # FILE FIXING
    # ------------------------------------------------------------------

    async def _fix_file(
        self,
        issue:     Dict,
        analysis:  Dict,
        file_path: str,
    ) -> Optional[Dict]:
        """
        Read one file, ask the LLM to fix it, validate the result,
        and return {"original": str, "fixed": str} or None.
        """
        # ── Read the file ──────────────────────────────────────────────
        file_data = self.github.get_file_content(file_path)
        if not file_data:
            self.logger.warning(f"Could not read: {file_path}")
            return None

        original: str = file_data["content"]

        if not original.strip():
            self.logger.warning(f"File is empty: {file_path}")
            return None

        # ── Build the prompt ───────────────────────────────────────────
        ext          = self._get_extension(file_path)
        lang         = self._ext_to_language(ext)
        approach     = analysis.get("approach", "Fix the bug described in the issue")
        issue_title  = issue.get("title", "")
        issue_body   = issue.get("body",  "")[:1000]

        # We intentionally avoid markdown fences inside the prompt
        # because they confuse the LLM into wrapping its output in fences.
        prompt = (
            "You are an expert software engineer.\n"
            "Your task is to fix a GitHub issue by modifying the file shown below.\n\n"
            f"ISSUE TITLE: {issue_title}\n"
            f"ISSUE DESCRIPTION:\n{issue_body}\n\n"
            f"SUGGESTED APPROACH: {approach}\n\n"
            f"FILE PATH: {file_path}\n"
            f"FILE LANGUAGE: {lang}\n\n"
            "FILE CONTENT (starts on the next line):\n"
            f"{original}\n\n"
            "RULES — follow these exactly:\n"
            "1. Return ONLY the complete fixed file content.\n"
            "2. Do NOT wrap the output in markdown fences or backticks.\n"
            "3. Do NOT add any explanation, preamble, or commentary.\n"
            "4. Keep the exact same coding style and formatting as the original.\n"
            "5. Make the smallest change necessary to fix the issue.\n"
            "6. Where you changed something, add a short inline comment:\n"
            "     Python  ->  # Fixed: <reason>\n"
            "     JS/TS   ->  // Fixed: <reason>\n"
            "     Other   ->  use the appropriate single-line comment syntax\n"
            "7. If you cannot safely fix the file, return the original content unchanged.\n\n"
            "Return the complete fixed file content now:"
        )

        messages = [
            {
                "role":    "system",
                "content": (
                    f"You are an expert {lang} developer. "
                    "Return ONLY the complete file content. "
                    "No markdown, no fences, no explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        # ── Call the LLM ───────────────────────────────────────────────
        raw_response = self.ollama.chat(messages, temperature=0.15)

        if not raw_response:
            self.logger.error(f"LLM returned empty response for: {file_path}")
            return None

        # ── Clean the output ───────────────────────────────────────────
        fixed = self._clean_llm_output(raw_response, ext)

        # ── Check it actually changed ──────────────────────────────────
        if fixed.strip() == original.strip():
            self.logger.info(f"LLM made no changes to: {file_path}")
            return None

        # ── Validate the output ────────────────────────────────────────
        ok, reason = self._validate_output(original, fixed, file_path, ext)
        if not ok:
            self.logger.warning(f"Validation failed for {file_path}: {reason}")
            return None

        return {
            "original":  original,
            "fixed":     fixed,
            "file_path": file_path,
            "language":  lang,
        }

    # ------------------------------------------------------------------
    # OUTPUT CLEANING
    # ------------------------------------------------------------------

    def _clean_llm_output(self, raw: str, ext: str) -> str:
        """
        Remove any markdown artifacts that the LLM added despite instructions.

        Handles patterns like:
            ```python
            <code>
            ```
        or:
            Here is the fixed file:
            ```
            <code>
            ```
        """
        text = raw.strip()

        # Pattern 1: fenced block with optional language tag
        # Matches: ```python\n...\n``` or ```\n...\n```
        fenced = re.search(
            r"^```[a-zA-Z0-9_+-]*\n(.*?)^```",
            text,
            re.DOTALL | re.MULTILINE,
        )
        if fenced:
            return fenced.group(1).strip()

        # Pattern 2: single backtick fence without language
        fenced2 = re.search(r"^`{3}(.*?)`{3}", text, re.DOTALL)
        if fenced2:
            return fenced2.group(1).strip()

        # Pattern 3: strip stray leading/trailing backtick lines
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        # Pattern 4: strip common preamble lines the LLM sometimes adds
        preamble_patterns = [
            r"^here is",
            r"^here's",
            r"^the fixed",
            r"^fixed file",
            r"^updated file",
            r"^below is",
        ]
        while lines:
            first = lines[0].strip().lower()
            if any(re.match(p, first) for p in preamble_patterns):
                lines = lines[1:]
            else:
                break

        return "\n".join(lines).strip()

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def _validate_output(
        self,
        original:  str,
        fixed:     str,
        file_path: str,
        ext:       str,
    ) -> tuple:
        """
        Run sanity checks on the LLM output.
        Returns (True, "OK") or (False, reason_string).
        """
        # ── 1. Not empty ───────────────────────────────────────────────
        if not fixed or not fixed.strip():
            return False, "Fixed content is empty"

        # ── 2. Size sanity ─────────────────────────────────────────────
        orig_lines  = len(original.splitlines())
        fixed_lines = len(fixed.splitlines())

        if orig_lines > 0:
            ratio = fixed_lines / orig_lines

            if ratio > 3.0:
                return (
                    False,
                    f"Fixed file is {ratio:.1f}x larger than original "
                    f"({fixed_lines} vs {orig_lines} lines) — likely hallucination",
                )

            if ratio < 0.25:
                return (
                    False,
                    f"Fixed file lost {100 - ratio*100:.0f}% of lines "
                    f"({fixed_lines} vs {orig_lines}) — likely truncated",
                )

        # ── 3. No leftover markdown fences ────────────────────────────
        if "```" in fixed:
            return False, "Fixed content still contains markdown fences"

        # ── 4. Language-specific syntax check ─────────────────────────
        if ext == "py":
            ok, msg = self._check_python_syntax(fixed)
            if not ok:
                return False, msg

        elif ext == "json":
            ok, msg = self._check_json_syntax(fixed)
            if not ok:
                return False, msg

        # ── 5. Dangerous pattern guard ────────────────────────────────
        danger = self._check_dangerous_patterns(fixed)
        if danger:
            return False, f"Dangerous pattern detected: {danger}"

        return True, "OK"

    def _check_python_syntax(self, code: str) -> tuple:
        try:
            ast.parse(code)
            return True, "OK"
        except SyntaxError as e:
            return False, f"Python SyntaxError at line {e.lineno}: {e.msg}"

    def _check_json_syntax(self, code: str) -> tuple:
        try:
            json.loads(code)
            return True, "OK"
        except json.JSONDecodeError as e:
            return False, f"JSON decode error: {e}"

    def _check_dangerous_patterns(self, code: str) -> Optional[str]:
        """Return the matched pattern string if dangerous content found."""
        dangerous = [
            (r"rm\s+-rf\s+/",                   "rm -rf /"),
            (r"os\.system\s*\(\s*['\"]rm",       "os.system rm"),
            (r"subprocess.*shell\s*=\s*True.*input", "shell injection"),
            (r"DROP\s+TABLE\s+\w+",              "SQL DROP TABLE"),
            (r"DELETE\s+FROM\s+\w+\s*;",         "unbounded SQL DELETE"),
        ]
        for pattern, label in dangerous:
            if re.search(pattern, code, re.IGNORECASE):
                return label
        return None

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _get_extension(file_path: str) -> str:
        """Return the lowercase extension without the dot."""
        if "." not in file_path:
            return ""
        return file_path.rsplit(".", 1)[-1].lower()

    @staticmethod
    def _ext_to_language(ext: str) -> str:
        """Map a file extension to a human-readable language name."""
        mapping = {
            "py":   "Python",
            "js":   "JavaScript",
            "ts":   "TypeScript",
            "jsx":  "JavaScript",
            "tsx":  "TypeScript",
            "java": "Java",
            "go":   "Go",
            "rs":   "Rust",
            "rb":   "Ruby",
            "php":  "PHP",
            "c":    "C",
            "cpp":  "C++",
            "cs":   "C#",
            "html": "HTML",
            "css":  "CSS",
            "scss": "SCSS",
            "sh":   "Shell",
            "bash": "Shell",
            "md":   "Markdown",
            "sql":  "SQL",
            "yaml": "YAML",
            "yml":  "YAML",
            "json": "JSON",
            "toml": "TOML",
            "xml":  "XML",
        }
        return mapping.get(ext, "text")