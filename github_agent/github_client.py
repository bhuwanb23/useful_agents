from github import Github
from config import Config
import base64

class GitHubClient:
    def __init__(self):
        self.gh = Github(Config.GITHUB_TOKEN)
        self.repo = self.gh.get_repo(Config.GITHUB_REPO)
    
    # ──────────────────────────────────────
    # FETCH ISSUES
    # ──────────────────────────────────────
    def get_open_issues(self, labels=None, limit=5):
        """Fetch open issues from the repo"""
        issues = []
        
        try:
            if labels:
                # Filter by specific labels like 'bug', 'good-first-issue'
                gh_issues = self.repo.get_issues(
                    state='open',
                    labels=labels
                )
            else:
                gh_issues = self.repo.get_issues(state='open')
            
            for issue in gh_issues[:limit]:
                # Skip Pull Requests (they appear as issues in GitHub API)
                if issue.pull_request:
                    continue
                    
                issues.append({
                    'number': issue.number,
                    'title': issue.title,
                    'body': issue.body or "",
                    'labels': [l.name for l in issue.labels],
                    'comments': self._get_issue_comments(issue),
                    'url': issue.html_url
                })
                
        except Exception as e:
            print(f"Error fetching issues: {e}")
            
        return issues
    
    def _get_issue_comments(self, issue):
        """Get all comments from an issue for more context"""
        comments = []
        for comment in issue.get_comments():
            comments.append({
                'author': comment.user.login,
                'body': comment.body
            })
        return comments
    
    # ──────────────────────────────────────
    # FETCH REPO FILES
    # ──────────────────────────────────────
    def get_file_content(self, file_path, branch="main"):
        """Get content of a specific file"""
        try:
            file = self.repo.get_contents(file_path, ref=branch)
            content = base64.b64decode(file.content).decode('utf-8')
            return {
                'content': content,
                'sha': file.sha,
                'path': file_path
            }
        except Exception as e:
            print(f"File not found: {file_path} - {e}")
            return None
    
    def get_repo_structure(self, path="", branch="main"):
        """Get list of files in the repo"""
        files = []
        try:
            contents = self.repo.get_contents(path, ref=branch)
            for item in contents:
                if item.type == "file":
                    files.append(item.path)
                elif item.type == "dir":
                    # Recursively get files (limit depth)
                    files.extend(self.get_repo_structure(item.path, branch))
        except Exception as e:
            print(f"Error reading structure: {e}")
        return files
    
    # ──────────────────────────────────────
    # CREATE BRANCH
    # ──────────────────────────────────────
    def create_branch(self, branch_name, from_branch="main"):
        """Create a new branch for the fix"""
        try:
            # Get the SHA of the source branch
            source = self.repo.get_branch(from_branch)
            
            # Create new branch from it
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=source.commit.sha
            )
            print(f"✅ Branch created: {branch_name}")
            return True
        except Exception as e:
            print(f"❌ Error creating branch: {e}")
            return False
    
    # ──────────────────────────────────────
    # COMMIT CHANGES
    # ──────────────────────────────────────
    def commit_file(self, file_path, new_content, commit_message, branch_name):
        """Commit a changed file to a branch"""
        try:
            # Check if file exists to get its SHA
            try:
                existing_file = self.repo.get_contents(file_path, ref=branch_name)
                file_sha = existing_file.sha
                
                # Update existing file
                self.repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    sha=file_sha,
                    branch=branch_name
                )
            except:
                # Create new file if it doesn't exist
                self.repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    branch=branch_name
                )
            
            print(f"✅ Committed: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error committing: {e}")
            return False
    
    # ──────────────────────────────────────
    # CREATE PULL REQUEST
    # ──────────────────────────────────────
    def create_pull_request(self, title, body, branch_name, base_branch="main"):
        """Open a Pull Request"""
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=base_branch
            )
            print(f"✅ PR Created: {pr.html_url}")
            return pr
        except Exception as e:
            print(f"❌ Error creating PR: {e}")
            return None
    
    def add_label_to_issue(self, issue_number, label):
        """Add a label to an issue (e.g., 'in-progress')"""
        issue = self.repo.get_issue(issue_number)
        issue.add_to_labels(label)