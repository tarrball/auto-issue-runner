"""Pull request management for the auto issue runner."""

import logging
from typing import Dict, Any

from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class PRManager:
    """Handles pull request creation and management."""
    
    def __init__(self, github_client: GitHubClient):
        self.github_client = github_client
    
    async def create_pull_request(self, issue: Dict[str, Any], branch_name: str) -> Dict[str, Any]:
        """Create a pull request for the given issue and branch."""
        title = f"Fix #{issue['number']}: {issue['title']}"
        body = self._generate_pr_body(issue)
        
        logger.info(f"📝 Creating pull request: {title}")
        
        try:
            pr = await self.github_client.create_pull_request(
                title=title,
                body=body,
                head=branch_name
            )
            
            logger.info(f"✅ Successfully created PR #{pr['number']}: {pr['html_url']}")
            return pr
            
        except Exception as e:
            logger.error(f"❌ Failed to create pull request: {e}")
            raise
    
    def _generate_pr_body(self, issue: Dict[str, Any]) -> str:
        """Generate a comprehensive PR body from the issue."""
        body_parts = [
            "## Summary",
            "",
            f"This pull request addresses issue #{issue['number']}.",
            ""
        ]
        
        # Add issue description if available
        if issue.get('body'):
            body_parts.extend([
                "## Issue Description",
                "",
                issue['body'],
                ""
            ])
        
        # Add acceptance criteria
        body_parts.extend([
            "## Changes Made",
            "",
            "- [ ] Implemented the requested feature/fix",
            "- [ ] Followed existing code patterns and conventions", 
            "- [ ] Added appropriate error handling",
            "- [ ] Updated documentation if needed",
            "",
            "## Test Plan",
            "",
            "- [ ] Manual testing completed",
            "- [ ] Automated tests pass (if configured)",
            "- [ ] Build succeeds (if configured)",
            "",
            f"Closes #{issue['number']}",
            "",
            "---",
            "",
            "🤖 Generated with [Claude Code](https://claude.ai/code)",
            "",
            "Co-Authored-By: Claude <noreply@anthropic.com>"
        ])
        
        return "\n".join(body_parts)