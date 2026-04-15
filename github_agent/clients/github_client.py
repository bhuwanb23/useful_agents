# clients/github_client.py
# Single source of truth for ALL GitHub API calls

import base64
import logging
import time
from typing import Any, Dict, List, Optional

from github import Github, GithubException
from config.settings import Config


class GitHubClient:
    """
    Wraps PyGithub with:
      - Automatic rate-limit handling & retries
      - Convenience methods used by multiple agents
      - Centralised error logging
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 5          # seconds between retries

    def __init__(self):
        self.logger = logging.getLogger("clients.github")
        self._gh   = Github(Config.GITHUB_TOKEN)
        self.repo  = self._gh.get_repo(Config.GITHUB_REPO)
        self.logger.info(f"GitHub client connected → {Config.GITHUB_REPO}")

    # ──────────────────────────────────────────────────────────
    # RATE LIMIT HELPER
    # ──────────────────────────────────────────────────────────

    def _call(self, fn, *args, **kwargs):
        """Execute a GitHub API call with automatic retry on rate-limit."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return fn(*args, **kwargs)
            except GithubException as e:
                if e.status == 403 and "rate limit" in str(e).lower():
                    wait = self.RETRY_DELAY * attempt
                    self.logger.warning(
                        f"Rate-limited. Waiting {wait}s (attempt {attempt})"
                    )
                    time.sleep(wait)
                else:
                    self.logger.error(f"GitHub API error: {e}")
                    raise
        return None

    # ──────────────────────────────────────────────────────────
    # ISSUES
    # ──────────────────────────────────────────────────────────

    def get_open_issues(
        self,
        labels: Optional[List[str]] = None,
        limit:  int = 10,
    ) -> List[Dict]:
        """
        Fetch open issues (not PRs) from the repo.

        Args:
            labels: Filter by label names, e.g. ['bug', 'good-first-issue']
            limit:  Max number of issues to return

        Returns:
            List of issue dicts with keys:
            number, title, body, labels, comments, url
        """
        issues: List[Dict] = []

        try:
            kwargs: Dict[str, Any] = {"state": "open"}
            if labels:
                kwargs["labels"] = labels

            raw_issues = self._call(self.repo.get_issues, **kwargs)
            if not raw_issues:
                return []

            count = 0
            for issue in raw_issues:
                if count >= limit:
                    break
                if issue.pull_request:          # skip PRs
                    continue

                issues.append({
                    "number":   issue.number,
                    "title":    issue.title,
                    "body":     issue.body or "",
                    "labels":   [lb.name for lb in issue.labels],
                    "comments": self._get_comments(issue),
                    "url":      issue.html_url,
                    "author":   issue.user.login,
                    "created":  str(issue.created_at),
                })
                count += 1

        except Exception as e:
            self.logger.error(f"get_open_issues failed: {e}")

        return issues

    def _get_comments(self, issue) -> List[Dict]:
        """Return up to 10 comments from an issue."""
        comments = []
        try:
            for c in list(issue.get_comments())[:10]:
                comments.append({
                    "author": c.user.login,
                    "body":   c.body[:500],
                })
        except Exception:
            pass
        return comments

    def add_issue_comment(self, issue_number: int, body: str) -> bool:
        """Post a comment on an issue."""
        try:
            issue = self._call(self.repo.get_issue, issue_number)
            self._call(issue.create_comment, body)
            return True
        except Exception as e:
            self.logger.error(f"add_issue_comment failed: {e}")
            return False

    def add_label(self, issue_number: int, label: str) -> bool:
        """Add a label to an issue."""
        try:
            issue = self._call(self.repo.get_issue, issue_number)
            self._call(issue.add_to_labels, label)
            return True
        except Exception as e:
            self.logger.error(f"add_label failed: {e}")
            return False

    # ──────────────────────────────────────────────────────────
    # FILES
    # ──────────────────────────────────────────────────────────

    def get_file_content(
        self,
        file_path: str,
        branch: str = "main",
    ) -> Optional[Dict]:
        """
        Read a file from the repo.

        Returns:
            {"content": str, "sha": str, "path": str} or None
        """
        try:
            file_obj = self._call(
                self.repo.get_contents, file_path, ref=branch
            )
            if not file_obj:
                return None

            # Handle binary files gracefully
            try:
                content = base64.b64decode(file_obj.content).decode("utf-8")
            except UnicodeDecodeError:
                self.logger.warning(f"Skipping binary file: {file_path}")
                return None

            return {
                "content": content,
                "sha":     file_obj.sha,
                "path":    file_path,
                "size":    file_obj.size,
            }
        except GithubException as e:
            if e.status != 404:
                self.logger.error(f"get_file_content({file_path}): {e}")
            return None

    def get_repo_structure(
        self,
        path:   str = "",
        branch: str = "main",
        max_depth: int = 4,
        _depth: int = 0,
    ) -> List[str]:
        """
        Recursively list all file paths in the repo.

        Returns:
            Flat list of relative file paths
        """
        if _depth >= max_depth:
            return []

        files: List[str] = []
        try:
            contents = self._call(
                self.repo.get_contents, path, ref=branch
            )
            if not contents:
                return []

            for item in contents:
                if item.type == "file":
                    # Skip very large or binary files
                    if item.size < Config.MAX_FILE_SIZE:
                        files.append(item.path)
                elif item.type == "dir":
                    # Skip hidden / vendor dirs
                    if not item.name.startswith(".") and item.name not in (
                        "node_modules", "vendor", "__pycache__",
                        ".git", "dist", "build",
                    ):
                        files.extend(
                            self.get_repo_structure(
                                item.path, branch, max_depth, _depth + 1
                            )
                        )
        except Exception as e:
            self.logger.error(f"get_repo_structure({path}): {e}")

        return files

    # ──────────────────────────────────────────────────────────
    # BRANCHES
    # ──────────────────────────────────────────────────────────

    def create_branch(
        self,
        branch_name: str,
        from_branch: str = "main",
    ) -> bool:
        """Create a new branch from an existing one."""
        try:
            source = self._call(self.repo.get_branch, from_branch)
            self._call(
                self.repo.create_git_ref,
                ref=f"refs/heads/{branch_name}",
                sha=source.commit.sha,
            )
            self.logger.info(f"Branch created: {branch_name}")
            return True
        except GithubException as e:
            if e.status == 422:
                self.logger.warning(f"Branch already exists: {branch_name}")
                return True          # treat as success
            self.logger.error(f"create_branch failed: {e}")
            return False

    def branch_exists(self, branch_name: str) -> bool:
        """Check whether a branch exists."""
        try:
            self._call(self.repo.get_branch, branch_name)
            return True
        except Exception:
            return False

    def delete_branch(self, branch_name: str) -> bool:
        """Delete a branch (used for cleanup on failure)."""
        try:
            ref = self._call(
                self.repo.get_git_ref, f"heads/{branch_name}"
            )
            self._call(ref.delete)
            return True
        except Exception as e:
            self.logger.error(f"delete_branch failed: {e}")
            return False

    # ──────────────────────────────────────────────────────────
    # COMMITS
    # ──────────────────────────────────────────────────────────

    def commit_file(
        self,
        file_path:      str,
        new_content:    str,
        commit_message: str,
        branch_name:    str,
    ) -> bool:
        """
        Create or update a file in the given branch.

        Uses update_file if the file already exists,
        create_file otherwise.
        """
        try:
            existing = self.get_file_content(file_path, branch=branch_name)

            if existing:
                self._call(
                    self.repo.update_file,
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    sha=existing["sha"],
                    branch=branch_name,
                )
            else:
                self._call(
                    self.repo.create_file,
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    branch=branch_name,
                )

            self.logger.info(f"Committed: {file_path} → {branch_name}")
            return True

        except Exception as e:
            self.logger.error(f"commit_file({file_path}): {e}")
            return False

    # ──────────────────────────────────────────────────────────
    # PULL REQUESTS
    # ──────────────────────────────────────────────────────────

    def create_pull_request(
        self,
        title:       str,
        body:        str,
        branch_name: str,
        base_branch: str = "main",
    ) -> Optional[Any]:
        """
        Open a Pull Request.

        Returns the PR object (has .number, .html_url) or None.
        """
        try:
            pr = self._call(
                self.repo.create_pull,
                title=title,
                body=body,
                head=branch_name,
                base=base_branch,
            )
            self.logger.info(f"PR created: #{pr.number} → {pr.html_url}")
            return pr
        except GithubException as e:
            if e.status == 422:
                self.logger.warning("PR already exists for this branch")
            else:
                self.logger.error(f"create_pull_request failed: {e}")
            return None

    def get_pull_request(self, pr_number: int) -> Optional[Any]:
        """Fetch a PR by number."""
        try:
            return self._call(self.repo.get_pull, pr_number)
        except Exception as e:
            self.logger.error(f"get_pull_request({pr_number}): {e}")
            return None

    def list_open_prs(self) -> List[Dict]:
        """List all open PRs (for deduplication checks)."""
        try:
            prs = self._call(self.repo.get_pulls, state="open")
            return [
                {
                    "number": pr.number,
                    "title":  pr.title,
                    "head":   pr.head.ref,
                    "url":    pr.html_url,
                }
                for pr in (prs or [])
            ]
        except Exception as e:
            self.logger.error(f"list_open_prs failed: {e}")
            return []

    # ──────────────────────────────────────────────────────────
    # REPO META
    # ──────────────────────────────────────────────────────────

    def get_default_branch(self) -> str:
        """Return the repo's default branch name."""
        try:
            return self.repo.default_branch
        except Exception:
            return "main"

    def get_languages(self) -> Dict[str, int]:
        """Return language breakdown: {"Python": 12345, ...}"""
        try:
            return dict(self._call(self.repo.get_languages) or {})
        except Exception:
            return {}