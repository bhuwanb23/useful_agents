from ollama_client import OllamaClient
from github_client import GitHubClient

class CodeGenerator:
    def __init__(self):
        self.ollama = OllamaClient()
        self.github = GitHubClient()
    
    def find_relevant_files(self, issue, repo_files, analysis):
        """Find which files are relevant to the issue"""
        relevant = []
        
        # Files suggested by Ollama
        suggested = analysis.get('files_to_check', [])
        
        for suggested_file in suggested:
            # Exact match
            if suggested_file in repo_files:
                relevant.append(suggested_file)
            else:
                # Fuzzy match - look for similar file names
                for repo_file in repo_files:
                    if suggested_file.lower() in repo_file.lower():
                        relevant.append(repo_file)
                        break
        
        # Also search by keywords in issue title
        keywords = issue['title'].lower().split()
        for repo_file in repo_files:
            file_lower = repo_file.lower()
            if any(kw in file_lower for kw in keywords if len(kw) > 3):
                if repo_file not in relevant:
                    relevant.append(repo_file)
        
        return relevant[:5]  # Limit to 5 files max
    
    def generate_fixes(self, issue, analysis):
        """Generate fixes for all relevant files"""
        fixes = {}
        
        # Get repo structure
        repo_files = self.github.get_repo_structure()
        
        # Find relevant files
        relevant_files = self.find_relevant_files(issue, repo_files, analysis)
        
        print(f"📁 Relevant files found: {relevant_files}")
        
        for file_path in relevant_files:
            print(f"🔧 Generating fix for: {file_path}")
            
            # Get current file content
            file_data = self.github.get_file_content(file_path)
            if not file_data:
                continue
            
            # Generate fix using Ollama
            fixed_content = self.ollama.generate_fix(
                issue=issue,
                file_content=file_data['content'],
                file_path=file_path
            )
            
            if fixed_content and fixed_content != file_data['content']:
                fixes[file_path] = {
                    'original': file_data['content'],
                    'fixed': fixed_content
                }
                print(f"✅ Fix generated for {file_path}")
            else:
                print(f"⏭️ No changes needed for {file_path}")
        
        return fixes