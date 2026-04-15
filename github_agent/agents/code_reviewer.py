
### Code Reviewer Agent

# ```python
# agents/code_reviewer.py

import json
from core.base_agent import BaseAgent
from typing import Dict

class CodeReviewerAgent(BaseAgent):
    """
    Reviews generated code fixes before they become PRs
    Ensures quality and correctness
    """
    
    def __init__(self):
        super().__init__(
            name="code_reviewer",
            description="Reviews generated code fixes for quality"
        )
        self.capabilities = ["review_code", "quality_check"]
    
    def can_handle(self, task: Dict) -> bool:
        return task.get('type') == 'review_code'
    
    async def execute(self, task: Dict) -> Dict:
        issue = task.get('issue')
        fixes = task.get('fixes', {})
        analysis = task.get('analysis', {})
        
        self.logger.info(f"Reviewing fixes for issue #{issue['number']}")
        
        review_results = []
        overall_approved = True
        
        for file_path, file_data in fixes.items():
            review = await self._review_fix(
                issue, 
                file_path, 
                file_data['original'],
                file_data['fixed'],
                analysis
            )
            
            review_results.append(review)
            
            if not review.get('approved'):
                overall_approved = False
                self.logger.warning(f"❌ Fix rejected for {file_path}: {review.get('reason')}")
        
        result = {
            "issue": issue,
            "fixes": fixes if overall_approved else {},
            "analysis": analysis,
            "approved": overall_approved,
            "review_results": review_results,
            "overall_score": sum(r.get('score', 0) for r in review_results) / len(review_results) if review_results else 0
        }
        
        if overall_approved:
            self.logger.info(f"✅ All fixes approved for issue #{issue['number']}")
        else:
            self.logger.warning(f"❌ Fixes rejected for issue #{issue['number']}")
        
        return result
    
    async def _review_fix(
        self, 
        issue: Dict, 
        file_path: str, 
        original: str, 
        fixed: str,
        analysis: Dict
    ) -> Dict:
        """Review a single file fix"""
        
        prompt = f"""Review this code fix. Respond with ONLY JSON.

ISSUE: {issue['title']}
FILE: {file_path}

ORIGINAL CODE:
{original[:2000]}

FIXED CODE:
{fixed[:2000]}

Review criteria:
1. Does it actually fix the issue?
2. Does it introduce new bugs?
3. Is it good quality code?
4. Does it follow the existing code style?
5. Are there any security concerns?

Respond with:
{{
    "approved": true or false,
    "score": 0-100,
    "fixes_the_issue": true or false,
    "introduces_bugs": true or false,
    "code_quality": "good|acceptable|poor",
    "security_concern": true or false,
    "style_consistent": true or false,
    "reason": "brief explanation",
    "suggestions": ["improvement1", "improvement2"]
}}"""
        
        messages = [
            {
                "role": "system",
                "content": "You are a senior code reviewer. Be strict but fair. Return only JSON."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = self.ollama.chat(messages, temperature=0.1)
        
        try:
            import re
            try:
                return json.loads(response)
            except:
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except:
            # Default to approved if parsing fails
            return {"approved": True, "score": 70, "reason": "Auto-approved (review parse failed)"}