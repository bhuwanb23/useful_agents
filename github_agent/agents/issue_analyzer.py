# agents/issue_analyzer.py

import json
from core.base_agent import BaseAgent
from typing import Dict

class IssueAnalyzerAgent(BaseAgent):
    """
    Analyzes GitHub issues and decides:
    - What type of issue it is
    - Can it be auto-fixed?
    - What approach to take
    - Which files are affected
    """
    
    def __init__(self):
        super().__init__(
            name="issue_analyzer",
            description="Analyzes GitHub issues using LLM"
        )
        self.capabilities = ["analyze_issue", "classify_issue", "estimate_complexity"]
    
    def can_handle(self, task: Dict) -> bool:
        return task.get('type') == 'analyze_issue'
    
    async def execute(self, task: Dict) -> Dict:
        issue = task.get('issue')
        self.logger.info(f"Analyzing issue #{issue['number']}: {issue['title']}")
        
        # Get full repo context
        repo_files = self.github.get_repo_structure()
        
        # Build analysis prompt
        analysis = await self._analyze_with_llm(issue, repo_files)
        
        if not analysis:
            return {"success": False, "error": "Analysis failed"}
        
        # Store analysis in shared memory
        await self.memory.set(
            f"issue.{issue['number']}.analysis",
            analysis
        )
        
        await self.memory.update_issue(
            issue['number'],
            status='analyzed',
            analysis=json.dumps(analysis)
        )
        
        self.logger.info(
            f"✅ Issue #{issue['number']} analyzed - "
            f"Type: {analysis.get('issue_type')} | "
            f"Auto-fix: {analysis.get('can_autofix')}"
        )
        
        return {
            "issue": issue,
            "analysis": analysis,
            "repo_files": repo_files
        }
    
    async def _analyze_with_llm(self, issue: Dict, repo_files: list) -> Dict:
        """Use Ollama to analyze the issue"""
        
        prompt = f"""Analyze this GitHub issue and respond with ONLY valid JSON:

ISSUE #{issue['number']}
Title: {issue['title']}
Body: {issue['body'][:2000]}
Labels: {', '.join(issue.get('labels', []))}

Repository has these files:
{chr(10).join(repo_files[:50])}

Respond with this exact JSON structure:
{{
    "summary": "one sentence description",
    "issue_type": "bug|feature|documentation|refactor|security|performance",
    "complexity": "simple|medium|complex",
    "can_autofix": true or false,
    "confidence": 0-100,
    "reason": "why you can or cannot fix this",
    "files_to_modify": ["file1.py", "file2.py"],
    "approach": "step by step approach to fix",
    "estimated_lines_changed": 10,
    "risks": ["list", "of", "risks"],
    "requires_human_review": true or false
}}"""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert software engineer. Analyze GitHub issues and respond with valid JSON only. No markdown, no explanations."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = self.ollama.chat(messages, temperature=0.1)
        
        try:
            import re
            # Try direct parse first
            try:
                return json.loads(response)
            except:
                # Find JSON in response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            self.logger.error(f"Failed to parse analysis: {e}")
            return None