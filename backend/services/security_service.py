"""
Security Service - AI-Powered Vulnerability Scanning and Validation
Scans Python code for security vulnerabilities using Azure OpenAI via MCP
"""

import os
import httpx
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class SecurityService:
    """AI-powered security scanning and validation service"""
    
    def __init__(self):
        """Initialize SecurityService with MCP server configuration"""
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        self.project_root = Path(__file__).parent.parent.parent
        logger.info(f"SecurityService initialized with MCP: {self.mcp_server_url}")
    
    async def scan_repository(self) -> Dict[str, Any]:
        """
        Scan all Python files in the repository for security vulnerabilities.
        
        Returns:
            Dict with total files scanned, vulnerabilities list, and summary counts
        """
        try:
            logger.info("Starting repository security scan")
            
            # Find all Python files in backend/ directory
            backend_dir = self.project_root / "backend"
            python_files = []
            
            if backend_dir.exists():
                for file_path in backend_dir.rglob("*.py"):
                    # Skip __pycache__, test files, and __init__.py
                    if (
                        "__pycache__" not in str(file_path)
                        and not file_path.name.startswith("test_")
                        and file_path.name != "__init__.py"
                    ):
                        relative_path = str(file_path.relative_to(self.project_root))
                        python_files.append(relative_path)
            
            logger.info(f"Found {len(python_files)} Python files to scan")
            
            # Scan each file
            all_vulnerabilities = []
            for file_path in python_files:
                try:
                    vulnerabilities = await self.scan_file(file_path)
                    all_vulnerabilities.extend(vulnerabilities)
                except Exception as e:
                    logger.error(f"Error scanning {file_path}: {str(e)}")
                    continue
            
            # Calculate summary counts by severity
            summary = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
            
            for vuln in all_vulnerabilities:
                severity = vuln.get("severity", "low").lower()
                if severity in summary:
                    summary[severity] += 1
            
            logger.info(f"Scan complete: Found {len(all_vulnerabilities)} vulnerabilities")
            
            return {
                "total_files_scanned": len(python_files),
                "vulnerabilities": all_vulnerabilities,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error during repository scan: {str(e)}")
            return {
                "total_files_scanned": 0,
                "vulnerabilities": [],
                "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0}
            }
    
    async def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Scan a single file for security vulnerabilities using AI.
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            List of vulnerabilities found
        """
        try:
            logger.info(f"Scanning file: {file_path}")
            
            # Read file content
            full_path = self.project_root / file_path
            if not full_path.exists():
                logger.warning(f"File not found: {file_path}")
                return []
            
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Skip empty or very small files
            if len(code.strip()) < 50:
                logger.info(f"Skipping small file: {file_path}")
                return []
            
            # Analyze with AI
            vulnerabilities = await self._analyze_code_security(file_path, code)
            
            logger.info(f"Found {len(vulnerabilities)} vulnerabilities in {file_path}")
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {str(e)}")
            return []
    
    async def _analyze_code_security(
        self, file_path: str, code: str
    ) -> List[Dict[str, Any]]:
        """
        Use AI to analyze code for security vulnerabilities.
        
        Args:
            file_path: Path to the file
            code: File content
            
        Returns:
            List of vulnerabilities with line, severity, issue, CWE, recommendation
        """
        try:
            # Limit code size for AI analysis (first 2000 chars)
            code_snippet = code[:2000]
            if len(code) > 2000:
                code_snippet += "\n... (truncated)"
            
            system_message = """You are a security expert analyzing Python code for vulnerabilities.

Detect the following security issues:
- Hardcoded secrets (passwords, API keys, tokens, SECRET_KEY values)
- SQL injection (string concatenation in queries)
- XSS vulnerabilities (unescaped user input in HTML)
- Insecure cryptography (weak algorithms like MD5, SHA1, hardcoded keys)
- Authentication bypasses
- Missing input validation
- Insecure file operations (path traversal)
- Debug mode enabled
- Eval/exec usage with user input
- Insecure random number generation (random module for security)

Respond ONLY with a JSON array of vulnerabilities. Each vulnerability must have:
{
  "line": <line_number>,
  "severity": "critical"|"high"|"medium"|"low",
  "issue": "brief description",
  "cwe": "CWE-XXX",
  "recommendation": "how to fix"
}

If no vulnerabilities found, return an empty array: []"""

            prompt = f"""Analyze this Python code for security vulnerabilities:

File: {file_path}
```python
{code_snippet}
```

Return JSON array of vulnerabilities found. If code is secure, return empty array []."""

            url = f"{self.mcp_server_url}/analyze"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json={
                        "prompt": prompt,
                        "system_message": system_message
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                ai_response = result.get("result", "")
                
                # Parse JSON from response
                vulnerabilities = self._extract_json_from_response(ai_response)
                
                # Add file path to each vulnerability
                for vuln in vulnerabilities:
                    vuln["file"] = file_path
                
                logger.info(f"AI analysis complete for {file_path}: {len(vulnerabilities)} issues")
                return vulnerabilities
                
        except httpx.HTTPStatusError as e:
            logger.error(f"MCP server error during security analysis: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error analyzing code security: {str(e)}")
            return []
    
    def _extract_json_from_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Extract JSON array from AI response, handling various formats.
        
        Args:
            response: AI response text
            
        Returns:
            List of parsed vulnerabilities
        """
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        try:
            # Try to find JSON array in text using regex
            json_pattern = r'\[[\s\S]*\]'
            match = re.search(json_pattern, response)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Could not extract JSON from response: {str(e)}")
        
        # If all else fails, return empty list
        logger.warning("No valid JSON found in AI response")
        return []
    
    async def validate_security(self) -> Dict[str, Any]:
        """
        Validate overall application security and calculate risk score.
        
        Risk Score Calculation:
        - Start at 100 (perfect score)
        - Critical: -30 points each
        - High: -15 points each
        - Medium: -5 points each
        - Low: -1 point each
        
        Returns:
            Dict with risk_score, status, summary, recommendations, and total count
        """
        try:
            logger.info("Starting security validation")
            
            # Run repository scan
            scan_result = await self.scan_repository()
            
            summary = scan_result.get("summary", {})
            total_vulnerabilities = len(scan_result.get("vulnerabilities", []))
            
            # Calculate risk score
            risk_score = 100
            risk_score -= summary.get("critical", 0) * 30
            risk_score -= summary.get("high", 0) * 15
            risk_score -= summary.get("medium", 0) * 5
            risk_score -= summary.get("low", 0) * 1
            
            # Clamp to 0-100 range
            risk_score = max(0, min(100, risk_score))
            
            # Determine status
            if risk_score >= 80:
                status = "secure"
            elif risk_score >= 50:
                status = "needs_attention"
            else:
                status = "critical"
            
            # Generate recommendations
            recommendations = []
            
            if summary.get("critical", 0) > 0:
                recommendations.append(
                    f"URGENT: Fix {summary['critical']} critical vulnerabilities immediately"
                )
            
            if summary.get("high", 0) > 0:
                recommendations.append(
                    f"Address {summary['high']} high-severity vulnerabilities as soon as possible"
                )
            
            if summary.get("medium", 0) > 0:
                recommendations.append(
                    f"Review and fix {summary['medium']} medium-severity issues"
                )
            
            if summary.get("low", 0) > 0:
                recommendations.append(
                    f"Consider addressing {summary['low']} low-severity issues for best practices"
                )
            
            if total_vulnerabilities == 0:
                recommendations.append("No vulnerabilities detected. Continue following security best practices.")
            
            # Add general recommendations
            if status != "secure":
                recommendations.extend([
                    "Review code for hardcoded secrets and move to environment variables",
                    "Implement input validation and sanitization",
                    "Use parameterized queries to prevent SQL injection",
                    "Enable security headers and HTTPS in production",
                    "Regular dependency updates and security audits"
                ])
            
            logger.info(f"Security validation complete: Score={risk_score}, Status={status}")
            
            return {
                "risk_score": risk_score,
                "status": status,
                "summary": summary,
                "recommendations": recommendations,
                "total_vulnerabilities": total_vulnerabilities,
                "files_scanned": scan_result.get("total_files_scanned", 0)
            }
            
        except Exception as e:
            logger.error(f"Error during security validation: {str(e)}")
            return {
                "risk_score": 0,
                "status": "error",
                "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "recommendations": ["Error occurred during security validation"],
                "total_vulnerabilities": 0,
                "files_scanned": 0
            }
