import requests
import json
from config import Config

class OllamaClient:
    def __init__(self):
        self.base_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL
    
    def chat(self, messages, temperature=0.3):
        """Send messages to Ollama and get a response"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,  # Lower = more deterministic
                "num_ctx": 8192              # Context window
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data['message']['content']
        except Exception as e:
            print(f"Ollama error: {e}")
            return None
    
    def analyze_issue(self, issue):
        """Ask Ollama to analyze a GitHub issue"""
        messages = [
            {
                "role": "system",
                "content": """You are an expert software engineer analyzing GitHub issues.
                Your job is to:
                1. Understand what the issue is about
                2. Identify what type of fix is needed
                3. Determine which files might need changes
                4. Rate the complexity (simple/medium/complex)
                
                Respond in JSON format only."""
            },
            {
                "role": "user", 
                "content": f"""Analyze this GitHub issue:
                
Title: {issue['title']}
Body: {issue['body']}
Labels: {', '.join(issue['labels'])}

Comments:
{self._format_comments(issue['comments'])}

Respond with JSON:
{{
    "summary": "brief description of the issue",
    "issue_type": "bug|feature|documentation|refactor",
    "complexity": "simple|medium|complex",
    "files_to_check": ["list", "of", "likely", "files"],
    "approach": "how you would fix this",
    "can_autofix": true/false,
    "reason": "why you can or cannot auto-fix"
}}"""
            }
        ]
        
        response = self.chat(messages, temperature=0.1)
        
        try:
            # Extract JSON from response
            return json.loads(response)
        except:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return None
    
    def generate_fix(self, issue, file_content, file_path):
        """Generate a code fix for the issue"""
        messages = [
            {
                "role": "system",
                "content": """You are an expert software engineer.
                Your task is to fix a GitHub issue by modifying code.
                
                Rules:
                - Return ONLY the fixed/complete file content
                - No explanations, no markdown code blocks
                - Keep the same code style as the original
                - Make minimal necessary changes
                - Add comments where you changed something"""
            },
            {
                "role": "user",
                "content": f"""Fix this GitHub issue:

ISSUE TITLE: {issue['title']}
ISSUE DESCRIPTION: {issue['body']}

FILE: {file_path}
CURRENT CONTENT:
{file_content}

Return the complete fixed file content:"""
            }
        ]
        
        return self.chat(messages, temperature=0.2)
    
    def generate_pr_description(self, issue, changes_made):
        """Generate a nice PR description"""
        messages = [
            {
                "role": "system",
                "content": "You are a software engineer writing clear PR descriptions."
            },
            {
                "role": "user",
                "content": f"""Write a Pull Request description for this fix:

ISSUE: #{issue['number']} - {issue['title']}
ISSUE BODY: {issue['body']}

CHANGES MADE:
{changes_made}

Format with:
## Summary
## Changes Made  
## Testing
## Related Issue"""
            }
        ]
        
        return self.chat(messages, temperature=0.4)
    
    def _format_comments(self, comments):
        if not comments:
            return "No comments"
        formatted = []
        for c in comments[:5]:  # Limit to 5 comments
            formatted.append(f"- {c['author']}: {c['body'][:200]}")
        return "\n".join(formatted)