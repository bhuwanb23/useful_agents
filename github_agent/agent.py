from github_client import GitHubClient
from ollama_client import OllamaClient
from code_generator import CodeGenerator
from pr_creator import PRCreator
from config import Config

class GitHubAgent:
    def __init__(self):
        self.github = GitHubClient()
        self.ollama = OllamaClient()
        self.code_gen = CodeGenerator()
        self.pr_creator = PRCreator()
        
        print("🤖 GitHub Agent initialized")
        print(f"📦 Repo: {Config.GITHUB_REPO}")
        print(f"🧠 LLM: {Config.OLLAMA_MODEL}")
    
    def run(self):
        """Main agent loop"""
        print("\n" + "="*50)
        print("🚀 Starting GitHub Agent Run")
        print("="*50)
        
        # Step 1: Fetch issues
        print(f"\n📋 Fetching issues with labels: {Config.ISSUE_LABELS}")
        issues = self.github.get_open_issues(
            labels=Config.ISSUE_LABELS,
            limit=Config.MAX_ISSUES
        )
        
        if not issues:
            print("✅ No issues found matching criteria")
            return
        
        print(f"Found {len(issues)} issues to process")
        
        # Step 2: Process each issue
        results = []
        for issue in issues:
            result = self.process_issue(issue)
            results.append(result)
        
        # Step 3: Summary
        self.print_summary(results)
    
    def process_issue(self, issue):
        """Process a single issue"""
        print(f"\n{'='*40}")
        print(f"🔍 Processing Issue #{issue['number']}: {issue['title']}")
        print(f"{'='*40}")
        
        result = {
            'issue_number': issue['number'],
            'title': issue['title'],
            'status': 'failed',
            'pr_url': None,
            'reason': None
        }
        
        try:
            # Step 1: Analyze the issue with Ollama
            print("🧠 Analyzing issue with Ollama...")
            analysis = self.ollama.analyze_issue(issue)
            
            if not analysis:
                result['reason'] = "Failed to analyze issue"
                return result
            
            print(f"📊 Analysis: {analysis['summary']}")
            print(f"📊 Type: {analysis['issue_type']}")
            print(f"📊 Complexity: {analysis['complexity']}")
            print(f"📊 Can auto-fix: {analysis['can_autofix']}")
            
            # Step 2: Check if it can be auto-fixed
            if not analysis.get('can_autofix', False):
                result['status'] = 'skipped'
                result['reason'] = analysis.get('reason', 'Too complex for auto-fix')
                print(f"⏭️ Skipping: {result['reason']}")
                return result
            
            # Skip complex issues
            if analysis.get('complexity') == 'complex':
                result['status'] = 'skipped'
                result['reason'] = "Issue too complex for auto-fix"
                print("⏭️ Skipping: Too complex")
                return result
            
            # Step 3: Generate fixes
            print("⚙️ Generating code fixes...")
            fixes = self.code_gen.generate_fixes(issue, analysis)
            
            if not fixes:
                result['reason'] = "Could not generate any fixes"
                return result
            
            print(f"✅ Generated fixes for {len(fixes)} files")
            
            # Step 4: Create PR
            print("📝 Creating Pull Request...")
            pr = self.pr_creator.create_fix_pr(issue, fixes, analysis)
            
            if pr:
                result['status'] = 'success'
                result['pr_url'] = pr.html_url
                print(f"🎉 PR Created: {pr.html_url}")
            else:
                result['reason'] = "Failed to create PR"
                
        except Exception as e:
            result['reason'] = str(e)
            print(f"❌ Error processing issue: {e}")
        
        return result
    
    def print_summary(self, results):
        """Print a summary of the run"""
        print("\n" + "="*50)
        print("📊 AGENT RUN SUMMARY")
        print("="*50)
        
        success = [r for r in results if r['status'] == 'success']
        skipped = [r for r in results if r['status'] == 'skipped']
        failed = [r for r in results if r['status'] == 'failed']
        
        print(f"✅ Success: {len(success)}")
        print(f"⏭️ Skipped: {len(skipped)}")
        print(f"❌ Failed: {len(failed)}")
        
        if success:
            print("\n🎉 PRs Created:")
            for r in success:
                print(f"  - Issue #{r['issue_number']}: {r['pr_url']}")
        
        if skipped:
            print("\n⏭️ Skipped Issues:")
            for r in skipped:
                print(f"  - Issue #{r['issue_number']}: {r['reason']}")


# ──────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────
if __name__ == "__main__":
    agent = GitHubAgent()
    agent.run()