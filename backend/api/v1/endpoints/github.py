"""
GitHub Integration Endpoints
Handles GitHub webhooks and manual triggers for issue analysis and PR reviews
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import os

from backend.services.github_service import GitHubService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize GitHub service
github_service = GitHubService()


# Request/Response Models
class AnalysisResponse(BaseModel):
    """Response model for issue/PR analysis"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class WebhookResponse(BaseModel):
    """Response model for webhook handlers"""
    status: str
    message: str
    processing: bool = True


# ========================================
# Health Check
# ========================================

@router.get("/health")
async def github_health():
    """
    Health check for GitHub integration.
    
    Returns:
        status: Service health status
        github_configured: Whether GitHub credentials are configured
        repo: Repository name if configured
    """
    is_configured = github_service.is_configured()
    
    return {
        "status": "healthy" if is_configured else "not_configured",
        "github_configured": is_configured,
        "repo": github_service.github_repo if is_configured else None,
        "mcp_server": github_service.mcp_server_url
    }


# ========================================
# Webhook Handlers
# ========================================

@router.post("/webhook/issues", response_model=WebhookResponse, status_code=status.HTTP_202_ACCEPTED)
async def handle_issue_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    GitHub webhook handler for issue events.
    
    Accepts GitHub webhook payloads for issue events (opened, edited, reopened)
    and triggers AI analysis in the background.
    
    Expected webhook events:
    - issues.opened
    - issues.reopened
    - issues.edited
    
    Returns 202 Accepted immediately and processes in background.
    """
    try:
        # Parse webhook payload
        payload = await request.json()
        
        # Get event type from header
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        action = payload.get("action", "unknown")
        
        logger.info(f"Received GitHub webhook: {event_type}.{action}")
        
        # Only process relevant issue events
        if event_type != "issues":
            return WebhookResponse(
                status="ignored",
                message=f"Event type '{event_type}' is not supported",
                processing=False
            )
        
        # Process opened, reopened, or edited issues
        if action not in ["opened", "reopened", "edited"]:
            return WebhookResponse(
                status="ignored",
                message=f"Action '{action}' is not processed",
                processing=False
            )
        
        # Extract issue number
        issue = payload.get("issue", {})
        issue_number = issue.get("number")
        
        if not issue_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload: missing issue number"
            )
        
        # Check if service is configured
        if not github_service.is_configured():
            logger.warning("GitHub service not configured, skipping issue analysis")
            return WebhookResponse(
                status="error",
                message="GitHub service not configured",
                processing=False
            )
        
        # Schedule background analysis
        background_tasks.add_task(
            process_issue_analysis,
            issue_number=issue_number
        )
        
        logger.info(f"Scheduled analysis for issue #{issue_number}")
        
        return WebhookResponse(
            status="accepted",
            message=f"Issue #{issue_number} queued for analysis",
            processing=True
        )
        
    except Exception as e:
        logger.error(f"Error handling issue webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing error: {str(e)}"
        )


@router.post("/webhook/pull_request", response_model=WebhookResponse, status_code=status.HTTP_202_ACCEPTED)
async def handle_pr_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    GitHub webhook handler for pull request events.
    
    Accepts GitHub webhook payloads for PR events (opened, synchronize, reopened)
    and triggers AI review in the background.
    
    Expected webhook events:
    - pull_request.opened
    - pull_request.synchronize (new commits pushed)
    - pull_request.reopened
    
    Returns 202 Accepted immediately and processes in background.
    """
    try:
        # Parse webhook payload
        payload = await request.json()
        
        # Get event type from header
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        action = payload.get("action", "unknown")
        
        logger.info(f"Received GitHub webhook: {event_type}.{action}")
        
        # Only process pull_request events
        if event_type != "pull_request":
            return WebhookResponse(
                status="ignored",
                message=f"Event type '{event_type}' is not supported",
                processing=False
            )
        
        # Process opened, synchronize, or reopened PRs
        if action not in ["opened", "synchronize", "reopened"]:
            return WebhookResponse(
                status="ignored",
                message=f"Action '{action}' is not processed",
                processing=False
            )
        
        # Extract PR number
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        
        if not pr_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload: missing PR number"
            )
        
        # Check if service is configured
        if not github_service.is_configured():
            logger.warning("GitHub service not configured, skipping PR review")
            return WebhookResponse(
                status="error",
                message="GitHub service not configured",
                processing=False
            )
        
        # Schedule background review
        background_tasks.add_task(
            process_pr_review,
            pr_number=pr_number
        )
        
        logger.info(f"Scheduled review for PR #{pr_number}")
        
        return WebhookResponse(
            status="accepted",
            message=f"PR #{pr_number} queued for review",
            processing=True
        )
        
    except Exception as e:
        logger.error(f"Error handling PR webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing error: {str(e)}"
        )


# ========================================
# Manual Triggers (for testing)
# ========================================

@router.post("/manual/analyze-issue/{issue_number}", response_model=AnalysisResponse)
async def manual_analyze_issue(issue_number: int):
    """
    Manually trigger issue analysis (for testing without webhooks).
    
    Args:
        issue_number: GitHub issue number to analyze
        
    Returns:
        Analysis results including labels added and comment URL
    """
    try:
        logger.info(f"Manual analysis triggered for issue #{issue_number}")
        
        # Check if service is configured
        if not github_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub service not configured. Set GITHUB_TOKEN and GITHUB_REPO environment variables."
            )
        
        # Perform analysis
        result = await github_service.analyze_and_label_issue(issue_number)
        
        if result["success"]:
            return AnalysisResponse(
                success=True,
                message=f"Successfully analyzed issue #{issue_number}",
                details=result
            )
        else:
            return AnalysisResponse(
                success=False,
                message=result.get("error", "Analysis failed"),
                details=result
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual issue analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}"
        )


@router.post("/manual/review-pr/{pr_number}", response_model=AnalysisResponse)
async def manual_review_pr(pr_number: int):
    """
    Manually trigger PR review (for testing without webhooks).
    
    Args:
        pr_number: GitHub PR number to review
        
    Returns:
        Review results including comment URL
    """
    try:
        logger.info(f"Manual review triggered for PR #{pr_number}")
        
        # Check if service is configured
        if not github_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub service not configured. Set GITHUB_TOKEN and GITHUB_REPO environment variables."
            )
        
        # Perform review
        result = await github_service.review_pull_request(pr_number)
        
        if result["success"]:
            return AnalysisResponse(
                success=True,
                message=f"Successfully reviewed PR #{pr_number}",
                details=result
            )
        else:
            return AnalysisResponse(
                success=False,
                message=result.get("error", "Review failed"),
                details=result
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual PR review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review error: {str(e)}"
        )

@router.post(
    "/manual/create-autofix-pr/{issue_number}",
    response_model=Dict[str, Any],
    summary="Create auto-fix PR for an issue"
)
async def create_autofix_pr(issue_number: int):
    """Create an automated PR to fix an issue"""
    logger.info(f"Manual trigger: Creating auto-fix PR for issue #{issue_number}")
    
    result = await github_service.create_auto_fix_pr(issue_number)
    
    if result.get("success"):
        logger.info(f"✅ Auto-fix PR created: {result.get('pr_url')}")
    else:
        logger.warning(f"❌ Auto-fix PR failed: {result.get('error', 'Unknown error')}")
    
    return result

# ========================================
# Background Task Functions
# ========================================

async def process_issue_analysis(issue_number: int):
    """
    Background task to process issue analysis.
    
    This runs asynchronously after the webhook returns 202 Accepted.
    """
    try:
        logger.info(f"Background: Starting analysis for issue #{issue_number}")
        result = await github_service.analyze_and_label_issue(issue_number)
        
        if result["success"]:
            logger.info(f"Background: Successfully analyzed issue #{issue_number}")
        else:
            logger.error(f"Background: Failed to analyze issue #{issue_number}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Background: Error analyzing issue #{issue_number}: {str(e)}")


async def process_pr_review(pr_number: int):
    """
    Background task to process PR review.
    
    This runs asynchronously after the webhook returns 202 Accepted.
    """
    try:
        logger.info(f"Background: Starting review for PR #{pr_number}")
        result = await github_service.review_pull_request(pr_number)
        
        if result["success"]:
            logger.info(f"Background: Successfully reviewed PR #{pr_number}")
        else:
            logger.error(f"Background: Failed to review PR #{pr_number}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Background: Error reviewing PR #{pr_number}: {str(e)}")
