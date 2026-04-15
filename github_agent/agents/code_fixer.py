# agents/code_fixer.py

import json
from core.base_agent import BaseAgent
from typing import Dict, List

class CodeFixerAgent(BaseAgent):
    """
    The main coding agent
    - Reads relevant files
    - Generates fixes using LLM
    - Validates the output
    """
    
    def __init__(self):
        super().__init__(
            name="code_fixer",
            description="Generates code fixes for GitHub issues"
        )
        self.capabilities = ["fix_code", "generate_code", "modify_files"]
    
    def can_handle(self, task: Dict) -> bool:
        return task.get('type') == 'fix_code'
    
    async def execute(self, task: Dict) -> Dict:
        issue = task.get('issue')
        analysis = task.get('analysis')
        
        self.logger.info(f"Fixing issue #{issue['number']}")
        
        # Get files to modify
        files_to_modify = analysis.get('files_to_modify', [])
        
        if not files_to_modify:
            # Let LLM find the files
            files_to_modify = await self._find_relevant_files(issue, analysis)
        
        # Generate fixes for each file
        fixes = {}
        for file_path in files_to_modify[:5]:  # Max 5 files
            fix = await self._fix_file(issue, analysis, file_path)
            if fix:
                fixes[file_path] = fix
        
        if not fixes:
            return {"success": False, "error": "No fixes could be generated"}
        
        # Store fixes in memory
        await self.memory.set(
            f"issue.{issue['number']}.fixes",
            {k: {"original": v["original"][:500], "path": k} for k, v in fixes.items()}
        )
        
        await self.memory.update_issue(
            issue['number'],
            status='fixed',
            fixes=json.dumps(list(fixes.keys()))
        )
        
        self.logger.info(f"✅ Generated fixes for {len(fixes)} files")
        
        return {
            "issue": issue,
            "analysis": analysis,
            "fixes": fixes,
            "files_changed": list(fixes.keys())
        }
    
    async def _find_relevant_files(self, issue: Dict, analysis: Dict) -> List[str]:
        """Use LLM to find relevant files"""
        repo_files = self.github.get_repo_structure()
        
        prompt = f"""Given this issue, which files should be modified?

Issue: {issue['title']}
Description: {issue['body'][:500]}
Analysis: {analysis.get('approach', '')}

Available files:
{chr(10).join(repo_files)}

Return ONLY a JSON array of file paths:
["file1.py", "file2.py"]"""
        
        messages = [
            {"role": "system", "content": "Return only a JSON array of file paths."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.ollama.chat(messages, temperature=0.1)
        
        try:
            import re
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                files = json.loads(match.group())
                # Validate files exist in repo
                all_files = self.github.get_repo_structure()
                return [f for f in files if f in all_files]
        except:
            pass
        
        return []
    
    async def _fix_file(self, issue: Dict, analysis: Dict, file_path: str) -> Dict:
        """Generate fix for a single file"""
        
        # Get current file content
        file_data = self.github.get_file_content(file_path)
        if not file_data:
            self.logger.warning(f"Could not read file: {file_path}")
            return None
        
        original_content = file_data['content']
        
        # Determine file type
        file_ext = file_path.split('.')[-1] if '.' in file_path else 'txt'
        
        prompt = f"""Fix this issue in the file below.

ISSUE: {issue['title']}
DESCRIPTION: {issue['body'][:1000]}
APPROACH: {analysis.get('approach', 'Fix the bug described in the issue')}

FILE: {file_path}
CONTENT:
```{file_ext}
{original_content}