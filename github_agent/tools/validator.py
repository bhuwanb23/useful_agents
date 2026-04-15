# tools/validator.py
# Validates LLM outputs before they touch the repo

import ast
import json
import logging
import re
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Tuple


class Validator:
    """
    Validates generated code and other LLM outputs.

    Checks:
      - Syntax correctness
      - Size sanity (not too big / too small)
      - Encoding issues
      - Dangerous patterns
    """

    # Patterns that should NEVER appear in generated code
    BLOCKLIST = [
        r"rm\s+-rf\s+/",              # dangerous shell command
        r"os\.system\s*\(\s*['\"]rm", # python rm
        r"DROP\s+TABLE",               # SQL drop table
        r"DELETE\s+FROM\s+\w+\s*;",   # unbounded SQL delete
        r"subprocess.*shell\s*=\s*True.*input",  # shell injection
    ]

    def __init__(self):
        self.logger = logging.getLogger("tools.validator")

    # ──────────────────────────────────────────────────────────
    # SIZE CHECKS
    # ──────────────────────────────────────────────────────────

    def check_size(
        self,
        original: str,
        fixed:    str,
        max_growth_pct: float = 200.0,
        min_size_pct:   float = 30.0,
    ) -> Tuple[bool, str]:
        """
        Ensure the fixed file hasn't ballooned or shrunk suspiciously.

        Returns: (ok: bool, reason: str)
        """
        orig_len  = max(len(original), 1)
        fixed_len = len(fixed)

        growth_pct = (fixed_len / orig_len) * 100

        if growth_pct > max_growth_pct:
            return (
                False,
                f"Fixed file is {growth_pct:.0f}% of original size (max {max_growth_pct}%)",
            )

        if growth_pct < min_size_pct:
            return (
                False,
                f"Fixed file is only {growth_pct:.0f}% of original size (min {min_size_pct}%)",
            )

        return True, "Size OK"

    # ──────────────────────────────────────────────────────────
    # SYNTAX CHECKS
    # ──────────────────────────────────────────────────────────

    def check_syntax(self, code: str, file_path: str) -> Tuple[bool, str]:
        """
        Syntax-check the code for known languages.

        Returns: (ok: bool, message: str)
        """
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""

        if ext == "py":
            return self._check_python_syntax(code)

        elif ext == "json":
            return self._check_json_syntax(code)

        elif ext in ("yaml", "yml"):
            return self._check_yaml_syntax(code)

        # For other languages just return True (no quick checker)
        return True, "No syntax checker for this language"

    def _check_python_syntax(self, code: str) -> Tuple[bool, str]:
        try:
            ast.parse(code)
            return True, "Python syntax OK"
        except SyntaxError as e:
            return False, f"Python SyntaxError at line {e.lineno}: {e.msg}"

    def _check_json_syntax(self, code: str) -> Tuple[bool, str]:
        try:
            json.loads(code)
            return True, "JSON syntax OK"
        except json.JSONDecodeError as e:
            return False, f"JSON error: {e}"

    def _check_yaml_syntax(self, code: str) -> Tuple[bool, str]:
        try:
            import yaml  # optional dep
            yaml.safe_load(code)
            return True, "YAML syntax OK"
        except ImportError:
            return True, "PyYAML not installed, skipping YAML check"
        except Exception as e:
            return False, f"YAML error: {e}"

    # ──────────────────────────────────────────────────────────
    # DANGEROUS PATTERN CHECK
    # ──────────────────────────────────────────────────────────

    def check_dangerous_patterns(self, code: str) -> Tuple[bool, List[str]]:
        """
        Scan for hard-blocked patterns.

        Returns: (safe: bool, matches: list[str])
        """
        found = []
        for pattern in self.BLOCKLIST:
            if re.search(pattern, code, re.IGNORECASE):
                found.append(pattern)

        return len(found) == 0, found

    # ──────────────────────────────────────────────────────────
    # ENCODING CHECK
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def check_encoding(code: str) -> Tuple[bool, str]:
        """Ensure the text is valid UTF-8."""
        try:
            code.encode("utf-8").decode("utf-8")
            return True, "Encoding OK"
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            return False, f"Encoding error: {e}"

    # ──────────────────────────────────────────────────────────
    # COMBINED FULL VALIDATION
    # ──────────────────────────────────────────────────────────

    def validate_fix(
        self,
        original:  str,
        fixed:     str,
        file_path: str,
    ) -> Dict:
        """
        Run all checks and return a combined result.

        Returns:
            {
                "valid":    bool,
                "checks":   {check_name: {"ok": bool, "msg": str}},
                "errors":   [str],
                "warnings": [str],
            }
        """
        checks  = {}
        errors  = []
        warnings = []

        # 1. Empty check
        if not fixed or not fixed.strip():
            return {
                "valid": False,
                "checks": {},
                "errors": ["Fixed content is empty"],
                "warnings": [],
            }

        # 2. Size check
        size_ok, size_msg = self.check_size(original, fixed)
        checks["size"] = {"ok": size_ok, "msg": size_msg}
        if not size_ok:
            errors.append(size_msg)

        # 3. Syntax check
        syn_ok, syn_msg = self.check_syntax(fixed, file_path)
        checks["syntax"] = {"ok": syn_ok, "msg": syn_msg}
        if not syn_ok:
            errors.append(syn_msg)

        # 4. Dangerous patterns
        safe, matches = self.check_dangerous_patterns(fixed)
        checks["safety"] = {
            "ok":  safe,
            "msg": "No dangerous patterns" if safe else f"Found: {matches}",
        }
        if not safe:
            errors.append(f"Dangerous patterns detected: {matches}")

        # 5. Encoding
        enc_ok, enc_msg = self.check_encoding(fixed)
        checks["encoding"] = {"ok": enc_ok, "msg": enc_msg}
        if not enc_ok:
            errors.append(enc_msg)

        # 6. Markdown leak (LLM sometimes wraps in ```)
        if "```" in fixed:
            warnings.append("Fixed content contains markdown fences — may need cleanup")

        overall = len(errors) == 0

        if overall:
            self.logger.info(f"✅ Validation passed: {file_path}")
        else:
            self.logger.warning(
                f"❌ Validation failed: {file_path} | Errors: {errors}"
            )

        return {
            "valid":    overall,
            "checks":   checks,
            "errors":   errors,
            "warnings": warnings,
        }

    def validate_json_response(self, raw: str, required_keys: List[str]) -> Tuple[bool, Optional[Dict], str]:
        """
        Validate that an LLM response is valid JSON with required keys.

        Returns: (ok, parsed_dict_or_None, error_msg)
        """
        if not raw:
            return False, None, "Empty response"

        # Try to parse
        data = None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            try:
                m = re.search(r"\{.*\}", raw, re.DOTALL)
                if m:
                    data = json.loads(m.group())
            except Exception:
                pass

        if data is None:
            return False, None, "Could not parse JSON from response"

        # Check required keys
        missing = [k for k in required_keys if k not in data]
        if missing:
            return False, 