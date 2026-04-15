# agents/test_writer.py

import json
import re
from core.base_agent import BaseAgent
from typing import Dict

class TestWriterAgent(BaseAgent):
    """
    Writes tests for the generated fixes
    """
    
    def __init__(self):
        super().__init__(
            name="test_writer",
            description="Writes automated tests for code fixes"
        )
        self.capabilities = ["write_tests", "generate_tests"]
    
    def can_handle(self, task: Dict) -> bool:
        return task.get('type') == 'write_tests'
    
    async def execute(self, task: Dict) -> Dict:
        issue = task.get('issue')
        fixes = task.get('fixes', {})
        
        self.logger.info(f"Writing tests for issue #{issue['number']}")
        
        tests = {}
        for file_path, file_data in fixes.items():
            test_code = await self._write_tests(issue, file_path, file_data)
            if test_code:
                test_file_path = self._get_test_file_path(file_path)
                tests[test_file_path] = test_code
        
        return {
            "issue": issue,
            "fixes": fixes,
            "tests": tests
        }
    
    async def _write_tests(self, issue: Dict, file_path: str, file_data: Dict) -> str:
        """Generate tests for a fixed file"""
        
        file_ext = file_path.split('.')[-1]
        
        # Determine test framework
        if file_ext == 'py':
            framework = "pytest"
        elif file_ext in ['js', 'ts']:
            framework = "jest"
        else:
            framework = "generic"
        
        prompt = f"""Write tests for this fix. Return ONLY the test code.

ISSUE FIXED: {issue['title']}
ORIGINAL CODE:
{file_data['original'][:1500]}

FIXED CODE:
{file_data['fixed'][:1500]}

Write {framework} tests that:
1. Test the bug is fixed
2. Test edge cases
3. Test existing functionality still works

Return ONLY the test code, no explanations:"""
        
        messages = [
            {
                "role": "system",
                "content": f"Write {framework} tests. Return only code, no markdown."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = self.ollama.chat(messages, temperature=0.2)
        
        # Clean up markdown
        response = re.sub(r'```\w*\n?', '', response).strip()
        
        return response
    
    def _get_test_file_path(self, file_path: str) -> str:
        """Generate test file path from source file path"""
        if file_path.endswith('.py'):
            # src/module.py -> tests/test_module.py
            filename = file_path.split('/')[-1]
            return f"tests/test_{filename}"
        elif file_path.endswith(('.js', '.ts')):
            return file_path.replace('.js', '.test.js').replace('.ts', '.test.ts')
        else:
            return f"tests/test_{file_path.split('/')[-1]}"