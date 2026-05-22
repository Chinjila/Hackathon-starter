"""
Security API Endpoints - Vulnerability Scanning and Validation
AI-powered security scanning using Azure OpenAI via MCP
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from datetime import datetime
import logging

from backend.services.security_service import SecurityService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/scan-repository",
    response_model=Dict[str, Any],
    summary="Scan repository for security vulnerabilities"
)
async def scan_repository():
    """
    Scan all Python files in the repository for security vulnerabilities.
    
    Uses AI to analyze code and detect:
    - Hardcoded secrets (passwords, API keys, tokens)
    - SQL injection vulnerabilities
    - XSS vulnerabilities
    - Insecure cryptography
    - Authentication bypasses
    - Missing input validation
    - Insecure file operations
    - Debug mode in production
    - Eval/exec with user input
    - Insecure random number generation
    
    Returns:
        - total_files_scanned: Number of files analyzed
        - vulnerabilities: List of detected vulnerabilities with severity
        - summary: Count by severity (critical, high, medium, low)
        - scan_timestamp: When the scan was performed
    
    Example:
    ```json
    {
      "total_files_scanned": 15,
      "vulnerabilities": [
        {
          "file": "backend/services/auth.py",
          "line": 42,
          "severity": "critical",
          "issue": "Hardcoded password detected",
          "cwe": "CWE-798",
          "recommendation": "Move password to environment variable"
        }
      ],
      "summary": {
        "critical": 1,
        "high": 3,
        "medium": 5,
        "low": 2
      },
      "scan_timestamp": "2026-02-18T10:30:00Z"
    }
    ```
    """
    try:
        logger.info("Starting repository security scan")
        
        # Initialize security service and run scan
        security_service = SecurityService()
        scan_result = await security_service.scan_repository()
        
        # Add timestamp
        scan_result["scan_timestamp"] = datetime.utcnow().isoformat()
        
        # Log results
        total_vulns = len(scan_result.get("vulnerabilities", []))
        logger.info(
            f"Repository scan complete: {scan_result['total_files_scanned']} files, "
            f"{total_vulns} vulnerabilities found"
        )
        
        return scan_result
        
    except Exception as e:
        logger.error(f"Error during repository scan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository scan failed: {str(e)}"
        )


@router.get(
    "/validate",
    response_model=Dict[str, Any],
    summary="Validate application security and get risk score"
)
async def validate_security():
    """
    Validate overall application security and calculate risk score.
    
    Performs a comprehensive security assessment including:
    - Full repository scan for vulnerabilities
    - Risk score calculation (0-100, where 100 is most secure)
    - Security status determination
    - Actionable recommendations
    
    Risk Score Calculation:
    - Start at 100 (perfect score)
    - Critical vulnerability: -30 points each
    - High severity: -15 points each
    - Medium severity: -5 points each
    - Low severity: -1 point each
    - Final score clamped to 0-100 range
    
    Security Status:
    - risk_score >= 80: "secure"
    - risk_score >= 50: "needs_attention"
    - risk_score < 50: "critical"
    
    Returns:
        - risk_score: 0-100 (100 = most secure)
        - status: "secure" | "needs_attention" | "critical"
        - summary: Vulnerability count by severity
        - recommendations: List of actionable recommendations
        - total_vulnerabilities: Total number of issues found
        - files_scanned: Number of files analyzed
    
    Example:
    ```json
    {
      "risk_score": 75,
      "status": "needs_attention",
      "summary": {
        "critical": 0,
        "high": 2,
        "medium": 3,
        "low": 5
      },
      "recommendations": [
        "Address 2 high-severity vulnerabilities as soon as possible",
        "Review and fix 3 medium-severity issues",
        "Consider addressing 5 low-severity issues for best practices"
      ],
      "total_vulnerabilities": 10,
      "files_scanned": 15
    }
    ```
    """
    try:
        logger.info("Starting security validation")
        
        # Initialize security service and run validation
        security_service = SecurityService()
        validation_result = await security_service.validate_security()
        
        # Log results
        logger.info(
            f"Security validation complete: Risk Score = {validation_result['risk_score']}, "
            f"Status = {validation_result['status']}"
        )
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error during security validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security validation failed: {str(e)}"
        )


@router.get(
    "/report",
    response_model=Dict[str, Any],
    summary="Get comprehensive security report"
)
async def get_security_report():
    """
    Get a comprehensive security report combining scan results and validation.
    
    This endpoint provides a complete security assessment including:
    - Full vulnerability scan results with details
    - Risk score and security status
    - Actionable recommendations
    - Summary statistics
    
    Returns:
        - scan_results: Full vulnerability scan data
          - total_files_scanned: Number of files analyzed
          - vulnerabilities: List of all detected vulnerabilities
          - summary: Count by severity
        - validation: Risk score and security status
          - risk_score: 0-100
          - status: "secure" | "needs_attention" | "critical"
          - recommendations: List of actionable items
        - timestamp: Report generation time
        - report_summary: Combined summary statistics
    
    Example:
    ```json
    {
      "scan_results": {
        "total_files_scanned": 15,
        "vulnerabilities": [...],
        "summary": {
          "critical": 1,
          "high": 3,
          "medium": 5,
          "low": 2
        }
      },
      "validation": {
        "risk_score": 70,
        "status": "needs_attention",
        "recommendations": [...]
      },
      "timestamp": "2026-02-18T10:30:00Z",
      "report_summary": {
        "total_vulnerabilities": 11,
        "files_scanned": 15,
        "risk_score": 70,
        "status": "needs_attention"
      }
    }
    ```
    """
    try:
        logger.info("Generating comprehensive security report")
        
        # Initialize security service
        security_service = SecurityService()
        
        # Run both scan and validation
        scan_results = await security_service.scan_repository()
        validation_results = await security_service.validate_security()
        
        # Generate timestamp
        report_timestamp = datetime.utcnow().isoformat()
        
        # Create combined summary
        report_summary = {
            "total_vulnerabilities": validation_results.get("total_vulnerabilities", 0),
            "files_scanned": scan_results.get("total_files_scanned", 0),
            "risk_score": validation_results.get("risk_score", 0),
            "status": validation_results.get("status", "unknown")
        }
        
        logger.info(
            f"Security report generated: {report_summary['total_vulnerabilities']} vulnerabilities, "
            f"Risk Score = {report_summary['risk_score']}"
        )
        
        return {
            "scan_results": scan_results,
            "validation": validation_results,
            "timestamp": report_timestamp,
            "report_summary": report_summary
        }
        
    except Exception as e:
        logger.error(f"Error generating security report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security report generation failed: {str(e)}"
        )


@router.get(
    "/health",
    summary="Security service health check"
)
async def security_health():
    """
    Health check for security scanning service.
    
    Returns service status and capabilities.
    
    Returns:
        - status: Service health status
        - service: Service name
        - ai_powered: Whether AI analysis is enabled
        - capabilities: List of security checks performed
    
    Example:
    ```json
    {
      "status": "healthy",
      "service": "security_scanner",
      "ai_powered": true,
      "capabilities": [
        "vulnerability_scanning",
        "risk_scoring",
        "code_analysis",
        "security_validation"
      ]
    }
    ```
    """
    try:
        # Test if SecurityService can be initialized
        security_service = SecurityService()
        
        return {
            "status": "healthy",
            "service": "security_scanner",
            "ai_powered": True,
            "capabilities": [
                "vulnerability_scanning",
                "risk_scoring",
                "code_analysis",
                "security_validation",
                "comprehensive_reporting"
            ],
            "mcp_server": security_service.mcp_server_url
        }
        
    except Exception as e:
        logger.error(f"Security service health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "security_scanner",
            "ai_powered": False,
            "error": str(e)
        }
