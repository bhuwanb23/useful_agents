# agents/security_scanner.py

import json
import re
from core.base_agent import BaseAgent
from typing import Dict, List

class SecurityScannerAgent(BaseAgent):
    """
    Scans code for security vulnerabilities
    Blocks PRs if serious issues found
    """
    
    def __init__(self):
        super().__init__(
            name="security_scanner",
            description="Scans code for security vulnerabilities"
        )
        self.capabilities = ["scan_security", "vulnerability_detection"]
        
        # Known dangerous patterns
        self.DANGEROUS_PATTERNS = {
            "sql_injection": [
                r"execute\s*\(\s*[\"'].*%.*[\"']",
                r"cursor\.execute\s*\(\s*f[\"']",
                r"\.format\(.*\).*execute"
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*[\"'][^\"']+[\"']",
                r"api_key\s*=\s*[\"'][^\"']+[\"']",
                r"secret\s*=\s*[\"'][^\"']+[\"']",
                r"token\s*=\s*[\"'][a-zA-Z0-9]{20,}[\"']"
            ],
            "command_injection": [
                r"os\.system\s*\(",
                r"subprocess\.call\s*\(.*shell\s*=\s*True",
                r"eval\s*\(",
                r"exec\s*\("
            ],
            "path_traversal": [
                r"\.\./",
                r"open\s*\(\s*.*\+.*\)"
            ],
            "xss": [
                r"innerHTML\s*=",
                r"document\.write\s*\("
            ]
        }
    
    def can_handle(self, task: Dict) -> bool:
        return task.get('type') == 'scan_security'
    
    async def execute(self, task: Dict) -> Dict:
        issue = task.get('issue')
        fixes = task.get('fixes', {})
        
        self.logger.info(f"🔒 Security scan for issue #{issue.get('number', 'unknown')}")
        
        all_vulnerabilities = []
        has_critical = False
        
        # Scan each fixed file
        for file_path, file_data in fixes.items():
            fixed_code = file_data.get('fixed', '')
            
            # Pattern-based scan
            pattern_vulns = self._pattern_scan(fixed_code, file_path)
            
            # LLM-based deep scan
            llm_vulns = await self._llm_security_scan(
                issue, file_path, fixed_code
            )
            
            file_vulns = pattern_vulns + llm_vulns
            
            for vuln in file_vulns:
                vuln['file'] = file_path
                if vuln.get('severity') == 'critical':
                    has_critical = True
            
            all_vulnerabilities.extend(file_vulns)
        
        result = {
            "issue": issue,
            "fixes": fixes,
            "has_vulnerabilities": len(all_vulnerabilities) > 0,
            "has_critical": has_critical,
            "vulnerabilities": all_vulnerabilities,
            "scan_passed": not has_critical,
            "total_found": len(all_vulnerabilities)
        }
        
        if has_critical:
            self.logger.error(f"🚨 CRITICAL security issues found! Blocking PR.")
        elif all_vulnerabilities:
            self.logger.warning(f"⚠️ {len(all_vulnerabilities)} security warnings found")
        else:
            self.logger.info("✅ Security scan passed")
        
        return result
    
    def _pattern_scan(self, code: str, file_path: str) -> List[Dict]:
        """Quick regex-based security scan"""
        vulnerabilities = []
        
        for vuln_type, patterns in self.DANGEROUS_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, code, re.IGNORECASE)
                for match in matches:
                    # Find line number
                    line_num = code[:match.start()].count('\n') + 1
                    
                    vulnerabilities.append({
                        "type": vuln_type,
                        "severity": "high",
                        "line": line_num,
                        "code": match.group()[:100],
                        "source": "pattern_scan"
                    })
        
        return vulnerabilities
    
    async def _llm_security_scan(
        self, 
        issue: Dict, 
        file_path: str, 
        code: str
    ) -> List[Dict]:
        """Deep LLM security analysis"""
        
        prompt = f"""Security audit this code. Return ONLY JSON.

FILE: {file_path}
CODE:
{code[:3000]}

Check for:
- SQL injection
- XSS vulnerabilities  
- Hardcoded credentials
- Command injection
- Insecure data handling
- Authentication flaws
- Input validation issues

Return:
{{
    "vulnerabilities": [
        {{
            "type": "vulnerability type",
            "severity": "critical|high|medium|low",
            "line": 0,
            "description": "what the vulnerability is",
            "fix": "how to fix it"
        }}
    ],
    "overall_security": "good|acceptable|poor"
}}"""
        
        messages = [
            {
                "role": "system",
                "content": "You are a security expert. Find real vulnerabilities, not false positives. Return only JSON."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = self.ollama.chat(messages, temperature=0.05)
        
        try:
            data = json.loads(response)
            return data.get('vulnerabilities', [])
        except:
            try:
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    return data.get('vulnerabilities', [])
            except:
                pass
        
        return []