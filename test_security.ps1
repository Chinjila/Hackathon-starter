# Security Scanner Test Script
# Tests AI-powered vulnerability scanning endpoints

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Zava AI Security Scanner Test Suite" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$BaseUrl = "http://localhost:8000/api/v1/security"
$OutputDir = "security-reports"

# Create output directory if it doesn't exist
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Function to display colored output based on severity
function Write-Vulnerability {
    param(
        [string]$Severity,
        [string]$Message
    )
    
    switch ($Severity.ToLower()) {
        "critical" { Write-Host $Message -ForegroundColor Red }
        "high" { Write-Host $Message -ForegroundColor DarkYellow }
        "medium" { Write-Host $Message -ForegroundColor Yellow }
        "low" { Write-Host $Message -ForegroundColor Green }
        default { Write-Host $Message }
    }
}

# Function to display status with color
function Write-Status {
    param(
        [string]$Status
    )
    
    switch ($Status.ToLower()) {
        "secure" { Write-Host $Status -ForegroundColor Green }
        "needs_attention" { Write-Host $Status -ForegroundColor Yellow }
        "critical" { Write-Host $Status -ForegroundColor Red }
        default { Write-Host $Status }
    }
}

# Test 1: Health Check
Write-Host "Test 1: Security Service Health Check" -ForegroundColor Magenta
Write-Host "--------------------------------------" -ForegroundColor Magenta

try {
    $healthResponse = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    Write-Host "Status: " -NoNewline
    Write-Host $healthResponse.status -ForegroundColor Green
    Write-Host "Service: $($healthResponse.service)"
    Write-Host "AI-Powered: $($healthResponse.ai_powered)"
    Write-Host "MCP Server: $($healthResponse.mcp_server)"
    Write-Host "`nCapabilities:" -ForegroundColor Cyan
    foreach ($capability in $healthResponse.capabilities) {
        Write-Host "  [OK] $capability" -ForegroundColor Gray
    }
    Write-Host "`n[OK] Health check passed!`n" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure the backend server is running on port 8000`n" -ForegroundColor Yellow
    exit 1
}

# Test 2: Repository Scan
Write-Host "Test 2: Full Repository Security Scan" -ForegroundColor Magenta
Write-Host "--------------------------------------" -ForegroundColor Magenta
Write-Host "Scanning all Python files... (This may take 30-60 seconds)`n" -ForegroundColor Yellow

try {
    $scanStartTime = Get-Date
    $scanResponse = Invoke-RestMethod -Uri "$BaseUrl/scan-repository" -Method Post
    $scanEndTime = Get-Date
    $scanDuration = ($scanEndTime - $scanStartTime).TotalSeconds
    
    Write-Host "[OK] Scan completed in $([math]::Round($scanDuration, 2)) seconds`n" -ForegroundColor Green
    
    # Display summary
    Write-Host "Scan Summary:" -ForegroundColor Cyan
    Write-Host "-------------" -ForegroundColor Cyan
    Write-Host "Files Scanned: $($scanResponse.total_files_scanned)"
    Write-Host "Total Vulnerabilities: $($scanResponse.vulnerabilities.Count)"
    Write-Host "Scan Timestamp: $($scanResponse.scan_timestamp)`n"
    
    # Display severity breakdown
    Write-Host "Severity Breakdown:" -ForegroundColor Cyan
    Write-Vulnerability -Severity "critical" -Message "  Critical: $($scanResponse.summary.critical)"
    Write-Vulnerability -Severity "high" -Message "  High:     $($scanResponse.summary.high)"
    Write-Vulnerability -Severity "medium" -Message "  Medium:   $($scanResponse.summary.medium)"
    Write-Vulnerability -Severity "low" -Message "  Low:      $($scanResponse.summary.low)"
    Write-Host ""
    
    # Display top 5 vulnerabilities
    if ($scanResponse.vulnerabilities.Count -gt 0) {
        Write-Host "Top 5 Vulnerabilities:" -ForegroundColor Cyan
        Write-Host "---------------------" -ForegroundColor Cyan
        
        $topVulns = $scanResponse.vulnerabilities | Select-Object -First 5
        $counter = 1
        
        foreach ($vuln in $topVulns) {
            Write-Host "`n$counter. " -NoNewline
            Write-Vulnerability -Severity $vuln.severity -Message "[$($vuln.severity.ToUpper())]"
            Write-Host "   File: $($vuln.file)" -ForegroundColor Gray
            Write-Host "   Line: $($vuln.line)" -ForegroundColor Gray
            Write-Host "   Issue: $($vuln.issue)" -ForegroundColor White
            if ($vuln.cwe) {
                Write-Host "   CWE: $($vuln.cwe)" -ForegroundColor Gray
            }
            Write-Host "   Recommendation: $($vuln.recommendation)" -ForegroundColor DarkCyan
            $counter++
        }
        
        if ($scanResponse.vulnerabilities.Count -gt 5) {
            $remaining = $scanResponse.vulnerabilities.Count - 5
            Write-Host "`n... and $remaining more vulnerabilities" -ForegroundColor Gray
        }
        
        Write-Host ""
    }
    else {
        Write-Host "[OK] No vulnerabilities found!`n" -ForegroundColor Green
    }
    
    # Save scan results
    $scanOutputPath = Join-Path $OutputDir "security-scan-results.json"
    $scanResponse | ConvertTo-Json -Depth 10 | Out-File $scanOutputPath
    Write-Host "[OK] Scan results saved to: $scanOutputPath" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "[ERROR] Repository scan failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 3: Security Validation
Write-Host "Test 3: Security Validation `& Risk Score" -ForegroundColor Magenta
Write-Host "----------------------------------------" -ForegroundColor Magenta

try {
    $validationResponse = Invoke-RestMethod -Uri "$BaseUrl/validate" -Method Get
    
    Write-Host "Risk Assessment:" -ForegroundColor Cyan
    Write-Host "----------------" -ForegroundColor Cyan
    
    # Display risk score with color bar
    $riskScore = $validationResponse.risk_score
    $barLength = [math]::Floor($riskScore / 2)
    $bar = "█" * $barLength
    
    Write-Host "Risk Score: " -NoNewline
    if ($riskScore -ge 80) {
        Write-Host "$riskScore/100 $bar" -ForegroundColor Green
    }
    elseif ($riskScore -ge 50) {
        Write-Host "$riskScore/100 $bar" -ForegroundColor Yellow
    }
    else {
        Write-Host "$riskScore/100 $bar" -ForegroundColor Red
    }
    
    Write-Host "Status: " -NoNewline
    Write-Status -Status $validationResponse.status
    Write-Host ""
    
    # Display vulnerability summary
    Write-Host "Vulnerability Summary:" -ForegroundColor Cyan
    Write-Vulnerability -Severity "critical" -Message "  Critical: $($validationResponse.summary.critical)"
    Write-Vulnerability -Severity "high" -Message "  High:     $($validationResponse.summary.high)"
    Write-Vulnerability -Severity "medium" -Message "  Medium:   $($validationResponse.summary.medium)"
    Write-Vulnerability -Severity "low" -Message "  Low:      $($validationResponse.summary.low)"
    Write-Host "  Total:    $($validationResponse.total_vulnerabilities)"
    Write-Host "  Files:    $($validationResponse.files_scanned)`n"
    
    # Display recommendations
    if ($validationResponse.recommendations.Count -gt 0) {
        Write-Host "Recommendations:" -ForegroundColor Cyan
        Write-Host "----------------" -ForegroundColor Cyan
        foreach ($rec in $validationResponse.recommendations) {
            Write-Host "  - $rec" -ForegroundColor Yellow
        }
        Write-Host ""
    }
}
catch {
    Write-Host "[ERROR] Security validation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 4: Comprehensive Security Report
Write-Host "Test 4: Comprehensive Security Report" -ForegroundColor Magenta
Write-Host "--------------------------------------" -ForegroundColor Magenta

try {
    $reportResponse = Invoke-RestMethod -Uri "$BaseUrl/report" -Method Get
    
    Write-Host "Report Generated: $($reportResponse.timestamp)" -ForegroundColor Gray
    Write-Host ""
    
    # Display report summary
    Write-Host "Report Summary:" -ForegroundColor Cyan
    Write-Host "---------------" -ForegroundColor Cyan
    Write-Host "Total Vulnerabilities: $($reportResponse.report_summary.total_vulnerabilities)"
    Write-Host "Files Scanned: $($reportResponse.report_summary.files_scanned)"
    Write-Host "Risk Score: $($reportResponse.report_summary.risk_score)/100"
    Write-Host "Status: " -NoNewline
    Write-Status -Status $reportResponse.report_summary.status
    Write-Host ""
    
    # Save full report
    $reportOutputPath = Join-Path $OutputDir "security-report-full.json"
    $reportResponse | ConvertTo-Json -Depth 10 | Out-File $reportOutputPath
    Write-Host "[OK] Full report saved to: $reportOutputPath" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "[ERROR] Report generation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Final Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Test Suite Complete" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "----------" -ForegroundColor Yellow
Write-Host "  1. Review the JSON reports in the '$OutputDir' directory"
Write-Host "  2. Address critical and high-severity vulnerabilities first"
Write-Host "  3. Run the scan again after fixes to verify improvements"
Write-Host "  4. Integrate security scanning into your CI/CD pipeline"
Write-Host "  5. Schedule regular security scans (weekly recommended)"
Write-Host ""

Write-Host "Available Reports:" -ForegroundColor Cyan
Write-Host "-----------------" -ForegroundColor Cyan
Get-ChildItem -Path $OutputDir -Filter "*.json" | ForEach-Object {
    $sizeKB = [math]::Round($_.Length / 1KB, 2)
    Write-Host "  FILE: $($_.Name) - Size: $sizeKB KB" -ForegroundColor Gray
}
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "-------------" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs#/security" -ForegroundColor Gray
Write-Host "  Scan Repository: POST /api/v1/security/scan-repository" -ForegroundColor Gray
Write-Host "  Validate Security: GET /api/v1/security/validate" -ForegroundColor Gray
Write-Host "  Full Report: GET /api/v1/security/report" -ForegroundColor Gray
Write-Host "  Health Check: GET /api/v1/security/health" -ForegroundColor Gray
Write-Host ""
