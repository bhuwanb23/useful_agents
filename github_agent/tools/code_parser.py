# tools/code_parser.py
# Understands code structure without running it
# Used by agents to get context before asking the LLM

import ast
import re
import logging
from typing import Dict, List, Optional, Tuple


class CodeParser:
    """
    Language-aware code analyser.

    Extracts:
      - Functions / methods and their signatures
      - Classes
      - Imports
      - TODO / FIXME / HACK comments
      - Complexity metrics
    """

    def __init__(self):
        self.logger = logging.getLogger("tools.code_parser")

    # ──────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────

    def parse(self, code: str, file_path: str = "") -> Dict:
        """
        Auto-detect language and parse the code.

        Returns a structured dict with everything found.
        """
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""

        if ext == "py":
            return self._parse_python(code, file_path)
        elif ext in ("js", "ts", "jsx", "tsx"):
            return self._parse_javascript(code, file_path)
        else:
            return self._parse_generic(code, file_path)

    # ──────────────────────────────────────────────────────────
    # PYTHON PARSER
    # ──────────────────────────────────────────────────────────

    def _parse_python(self, code: str, file_path: str) -> Dict:
        result = {
            "language":   "python",
            "file":       file_path,
            "functions":  [],
            "classes":    [],
            "imports":    [],
            "todos":      [],
            "metrics":    {},
            "errors":     [],
        }

        # Check for syntax errors first
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result["errors"].append(str(e))
            return result

        # Walk AST
        for node in ast.walk(tree):

            # Functions & methods
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                result["functions"].append({
                    "name":       node.name,
                    "line":       node.lineno,
                    "args":       args,
                    "is_async":   isinstance(node, ast.AsyncFunctionDef),
                    "docstring":  ast.get_docstring(node) or "",
                    "decorators": [
                        ast.unparse(d) for d in node.decorator_list
                    ] if hasattr(ast, "unparse") else [],
                })

            # Classes
            elif isinstance(node, ast.ClassDef):
                methods = [
                    n.name for n in ast.walk(node)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and n is not node
                ]
                result["classes"].append({
                    "name":      node.name,
                    "line":      node.lineno,
                    "methods":   methods,
                    "docstring": ast.get_docstring(node) or "",
                    "bases":     [
                        ast.unparse(b) for b in node.bases
                    ] if hasattr(ast, "unparse") else [],
                })

            # Imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    result["imports"].append(f"{module}.{alias.name}")

        # TODO / FIXME / HACK comments
        result["todos"] = self._extract_todos(code)

        # Basic metrics
        lines   = code.splitlines()
        result["metrics"] = {
            "total_lines":    len(lines),
            "blank_lines":    sum(1 for l in lines if not l.strip()),
            "comment_lines":  sum(1 for l in lines if l.strip().startswith("#")),
            "function_count": len(result["functions"]),
            "class_count":    len(result["classes"]),
            "import_count":   len(result["imports"]),
        }

        return result

    # ──────────────────────────────────────────────────────────
    # JAVASCRIPT / TYPESCRIPT PARSER (regex-based)
    # ──────────────────────────────────────────────────────────

    def _parse_javascript(self, code: str, file_path: str) -> Dict:
        result = {
            "language":  "javascript",
            "file":      file_path,
            "functions": [],
            "classes":   [],
            "imports":   [],
            "todos":     [],
            "metrics":   {},
            "errors":    [],
        }

        # Functions (function keyword + arrow functions)
        fn_patterns = [
            r"(?:async\s+)?function\s+(\w+)\s*\(",            # function foo(
            r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(", # const foo = (
            r"(\w+)\s*:\s*(?:async\s*)?\(",                     # method: (
        ]
        for i, line in enumerate(code.splitlines(), 1):
            for pattern in fn_patterns:
                m = re.search(pattern, line)
                if m:
                    result["functions"].append({
                        "name": m.group(1),
                        "line": i,
                    })

        # Classes
        for m in re.finditer(r"class\s+(\w+)", code):
            line = code[:m.start()].count("\n") + 1
            result["classes"].append({"name": m.group(1), "line": line})

        # Imports
        for m in re.finditer(
            r"(?:import|require)\s*[\({\"']([^\"'\)]+)[\"'\)}]", code
        ):
            result["imports"].append(m.group(1))

        result["todos"] = self._extract_todos(code)

        lines = code.splitlines()
        result["metrics"] = {
            "total_lines":    len(lines),
            "function_count": len(result["functions"]),
            "class_count":    len(result["classes"]),
        }

        return result

    # ──────────────────────────────────────────────────────────
    # GENERIC (any other language)
    # ──────────────────────────────────────────────────────────

    def _parse_generic(self, code: str, file_path: str) -> Dict:
        lines = code.splitlines()
        return {
            "language":  "unknown",
            "file":      file_path,
            "functions": [],
            "classes":   [],
            "imports":   [],
            "todos":     self._extract_todos(code),
            "metrics":   {"total_lines": len(lines)},
            "errors":    [],
        }

    # ──────────────────────────────────────────────────────────
    # SHARED HELPERS
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _extract_todos(code: str) -> List[Dict]:
        """Find TODO / FIXME / HACK / BUG / XXX comments."""
        todos  = []
        pattern = re.compile(
            r"#\s*(TODO|FIXME|HACK|BUG|XXX):?\s*(.*)", re.IGNORECASE
        )
        for i, line in enumerate(code.splitlines(), 1):
            m = pattern.search(line)
            if m:
                todos.append({
                    "type":    m.group(1).upper(),
                    "message": m.group(2).strip(),
                    "line":    i,
                })
        return todos

    def get_function_body(
        self,
        code: str,
        function_name: str,
    ) -> Optional[str]:
        """Extract the body of a specific function (Python only)."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == function_name
                ):
                    lines = code.splitlines()
                    start = node.lineno - 1
                    end   = node.end_lineno if hasattr(node, "end_lineno") else start + 20
                    return "\n".join(lines[start:end])
        except Exception:
            pass
        return None

    def summarize(self, code: str, file_path: str = "") -> str:
        """
        Return a short human-readable summary of the file.
        Used to give the LLM context without sending the whole file.
        """
        parsed = self.parse(code, file_path)
        parts  = []

        if parsed.get("classes"):
            names = [c["name"] for c in parsed["classes"]]
            parts.append(f"Classes: {', '.join(names)}")

        if parsed.get("functions"):
            names = [f["name"] for f in parsed["functions"]]
            parts.append(f"Functions: {', '.join(names[:10])}")

        if parsed.get("metrics"):
            m = parsed["metrics"]
            parts.append(
                f"Lines: {m.get('total_lines', 0)} | "
                f"Functions: {m.get('function_count', 0)} | "
                f"Classes: {m.get('class_count', 0)}"
            )

        if parsed.get("todos"):
            parts.append(f"TODOs: {len(parsed['todos'])}")

        return " | ".join(parts) if parts else "Empty file"