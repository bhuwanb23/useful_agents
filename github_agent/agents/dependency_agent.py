# agents/dependency_agent.py
# Checks for outdated / vulnerable dependencies
# Can open PRs to bump package versions

import re
import json
from typing import Dict, List, Optional, Tuple
from core.base_agent import BaseAgent


class DependencyAgent(BaseAgent):
    """
    Manages project dependencies:
      - Detects outdated packages
      - Finds known vulnerable versions
      - Suggests / applies safe version bumps
      - Opens PRs for dependency updates
    """

    def __init__(self):
        super().__init__(
            name="dependency_agent",
            description="Detects and fixes outdated/vulnerable dependencies"
        )
        self.capabilities = [
            "check_deps",
            "update_deps",
            "audit_deps",
        ]

        # Files that declare dependencies, by ecosystem
        self.DEP_FILES = {
            "python": ["requirements.txt", "requirements-dev.txt",
                       "Pipfile", "pyproject.toml", "setup.py"],
            "node":   ["package.json", "package-lock.json", "yarn.lock"],
            "ruby":   ["Gemfile", "Gemfile.lock"],
            "go":     ["go.mod", "go.sum"],
            "java":   ["pom.xml", "build.gradle"],
            "rust":   ["Cargo.toml", "Cargo.lock"],
        }

    # ──────────────────────────────────────────────────────────
    def can_handle(self, task: Dict) -> bool:
        return task.get("type") in ("check_deps", "update_deps", "audit_deps")

    # ──────────────────────────────────────────────────────────
    async def execute(self, task: Dict) -> Dict:
        task_type = task.get("type", "check_deps")
        issue     = task.get("issue", {})

        self.logger.info(f"🔍 Running dependency task: {task_type}")

        # Discover which dependency files exist in the repo
        dep_files = await self._find_dep_files()

        if not dep_files:
            self.logger.info("No dependency files found in repo")
            return {"dep_files": [], "issues": [], "updates": {}}

        all_issues:  List[Dict] = []
        all_updates: Dict[str, str] = {}

        for ecosystem, file_path, content in dep_files:
            self.logger.info(f"  Checking {file_path} ({ecosystem})")

            # Parse current deps
            deps = self._parse_deps(ecosystem, content)

            # Ask LLM to find problems and suggest updates
            scan_result = await self._scan_deps(ecosystem, file_path, content, deps)

            all_issues.extend(scan_result.get("issues", []))

            # If task is update_deps, apply suggested bumps
            if task_type == "update_deps":
                updated_content = await self._apply_updates(
                    ecosystem, content, scan_result.get("safe_updates", [])
                )
                if updated_content and updated_content != content:
                    all_updates[file_path] = updated_content

        # Build result
        result = {
            "issue":      issue,
            "dep_files":  [fp for _, fp, _ in dep_files],
            "issues":     all_issues,
            "updates":    all_updates,
            "has_issues": len(all_issues) > 0,
            "critical_count": sum(
                1 for i in all_issues if i.get("severity") == "critical"
            ),
        }

        if all_issues:
            self.logger.warning(
                f"⚠️  Found {len(all_issues)} dependency issue(s)"
            )
        else:
            self.logger.info("✅ All dependencies look healthy")

        # If updates were generated, create a PR
        if all_updates:
            await self._create_dep_pr(all_updates, all_issues)

        return result

    # ──────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────

    async def _find_dep_files(self) -> List[Tuple[str, str, str]]:
        """Return (ecosystem, file_path, content) for each dep file found."""
        found = []
        repo_files = self.github.get_repo_structure()

        for ecosystem, candidates in self.DEP_FILES.items():
            for candidate in candidates:
                # Direct match or anywhere in tree
                matches = [f for f in repo_files
                           if f == candidate or f.endswith(f"/{candidate}")]
                for match in matches:
                    data = self.github.get_file_content(match)
                    if data:
                        found.append((ecosystem, match, data["content"]))

        return found

    # ──────────────────────────────────────────────────────────

    def _parse_deps(self, ecosystem: str, content: str) -> List[Dict]:
        """Quick regex parse of dependency declarations."""
        deps = []

        if ecosystem == "python":
            # requirements.txt: package==1.2.3 or package>=1.0
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.match(r"^([\w\-]+)\s*([><=!~]+)\s*([\d\.\*]+)", line)
                if m:
                    deps.append({
                        "name":     m.group(1),
                        "operator": m.group(2),
                        "version":  m.group(3),
                        "raw":      line,
                    })

        elif ecosystem == "node":
            try:
                pkg = json.loads(content)
                for section in ("dependencies", "devDependencies"):
                    for name, ver in pkg.get(section, {}).items():
                        deps.append({"name": name, "version": ver, "section": section})
            except json.JSONDecodeError:
                pass

        # Other ecosystems: return raw (LLM will handle them)
        return deps

    # ──────────────────────────────────────────────────────────

    async def _scan_deps(
        self,
        ecosystem: str,
        file_path: str,
        content: str,
        parsed: List[Dict],
    ) -> Dict:
        """Ask Ollama to audit the dependency file."""

        prompt = f"""Audit these dependencies and respond with ONLY JSON.

ECOSYSTEM: {ecosystem}
FILE: {file_path}

DEPENDENCY FILE CONTENT:
{content[:3000]}

Check for:
1. Known vulnerable package versions
2. Severely outdated packages
3. Deprecated packages
4. Packages with known security CVEs

Respond with:
{{
    "issues": [
        {{
            "package":     "package-name",
            "current":     "1.0.0",
            "severity":    "critical|high|medium|low",
            "reason":      "why it is a problem",
            "cve":         "CVE-2024-XXXX or null"
        }}
    ],
    "safe_updates": [
        {{
            "package":     "package-name",
            "from":        "1.0.0",
            "to":          "1.2.3",
            "breaking":    false
        }}
    ],
    "overall_health": "good|fair|poor"
}}"""

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a dependency security expert. "
                    "Only flag real known issues, not speculation. "
                    "Return only valid JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response = self.ollama.chat(messages, temperature=0.05)

        try:
            return json.loads(response)
        except Exception:
            try:
                m = re.search(r"\{.*\}", response, re.DOTALL)
                if m:
                    return json.loads(m.group())
            except Exception:
                pass

        return {"issues": [], "safe_updates": [], "overall_health": "unknown"}

    # ──────────────────────────────────────────────────────────

    async def _apply_updates(
        self,
        ecosystem: str,
        content: str,
        updates: List[Dict],
    ) -> Optional[str]:
        """Apply version bumps to the dependency file content."""

        if not updates:
            return None

        updated = content
        for upd in updates:
            if upd.get("breaking"):
                continue           # Skip breaking changes

            pkg  = re.escape(upd["package"])
            frm  = re.escape(upd["from"])
            to   = upd["to"]

            # Python: replace ==old or >=old
            if ecosystem == "python":
                updated = re.sub(
                    rf"({pkg}\s*[><=!~]+\s*){frm}",
                    lambda m, t=to: m.group(1) + t,
                    updated,
                )
            # Node: replace "old" version string
            elif ecosystem == "node":
                updated = updated.replace(f'"{frm}"', f'"{to}"')

        return updated if updated != content else None

    # ──────────────────────────────────────────────────────────

    async def _create_dep_pr(self, updates: Dict[str, str], issues: List[Dict]):
        """Commit updated dependency files and open a PR."""

        branch = f"auto-fix/dependency-updates-{__import__('time').strftime('%Y%m%d')}"

        if not self.github.create_branch(branch):
            return

        for file_path, new_content in updates.items():
            self.github.commit_file(
                file_path=file_path,
                new_content=new_content,
                commit_message=f"chore(deps): update {file_path}",
                branch_name=branch,
            )

        # Build PR body
        issue_lines = "\n".join(
            f"- **{i['package']}** ({i['severity']}): {i['reason']}"
            for i in issues
        )

        body = f"""## 🔒 Dependency Updates

This PR updates vulnerable / outdated dependencies detected by the GitHub Agent.

### Issues Found
{issue_lines or 'See file diffs for details'}

### Files Changed
{chr(10).join(f'- `{f}`' for f in updates.keys())}

---
*🤖 Auto-generated by Dependency Agent*"""

        self.github.create_pull_request(
            title="chore(deps): update vulnerable/outdated dependencies",
            body=body,
            branch_name=branch,
        )