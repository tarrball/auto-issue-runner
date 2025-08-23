"""Issue selection and filtering logic."""

import logging
import re
from typing import Optional, Dict, Any, Set

from .github_client import GitHubClient
from .validators import validate_github_issue, sanitize_branch_name

logger = logging.getLogger(__name__)


class IssueSelector:
    """Handles issue selection and filtering logic."""
    
    def __init__(self, github_client: GitHubClient):
        self.github_client = github_client
        self.processed_issues: Set[int] = set()
    
    async def find_eligible_issue(self) -> Optional[Dict[str, Any]]:
        """
        Find the next eligible issue to process.
        Returns None if no issues available or if there are open PRs.
        """
        try:
            logger.info("🔍 Searching for eligible issues...")
            
            # First check if any open PRs exist from the bot
            open_prs = await self.github_client.get_open_pull_requests()
            
            if open_prs:
                logger.info("🚫 Skipping all issues - Claude has open PR(s):")
                for pr in open_prs:
                    logger.info(f"   - PR #{pr['number']}: {pr['title']} ({pr['head']['ref']})")
                return None
            
            # Search for eligible issues
            issues = await self.github_client.search_eligible_issues()
            
            if not issues:
                logger.info("📭 No eligible issues found")
                return None
            
            logger.info(f"📋 Found {len(issues)} eligible issues")
            
            # Filter out already processed issues in this session
            available_issues = []
            for issue in issues:
                if issue['number'] in self.processed_issues:
                    logger.info(f"   Skipping issue #{issue['number']}: Already processed in this session")
                    continue
                available_issues.append(issue)
            
            if not available_issues:
                logger.info("📝 No available issues (all were processed in this session)")
                return None
            
            # Select the oldest issue (first in sorted list)
            selected_issue = available_issues[0]
            issue_number = selected_issue['number']
            
            logger.info(f"✅ Selected issue #{issue_number}: {selected_issue['title']}")
            
            # Mark as processed
            self.processed_issues.add(issue_number)
            
            # Get detailed issue information
            detailed_issue = await self.github_client.get_issue(issue_number)
            
            # Validate issue data for security
            if not validate_github_issue(detailed_issue):
                logger.warning(f"Issue #{issue_number} failed validation, skipping")
                return None
            
            return detailed_issue
            
        except Exception as e:
            logger.error(f"❌ Error finding eligible issue: {e}")
            raise
    
    def generate_branch_name(self, issue: Dict[str, Any]) -> str:
        """
        Generate a git branch name from an issue.
        Format: auto/<issue-number>-<sanitized-title-slug>
        """
        title = issue['title']
        
        # Sanitize title to create a URL-friendly slug
        slug = re.sub(r'[^a-z0-9\s-]', '', title.lower())  # Remove special chars
        slug = re.sub(r'\s+', '-', slug)  # Replace spaces with hyphens
        slug = slug[:40]  # Limit length
        slug = re.sub(r'-+$', '', slug)  # Remove trailing hyphens
        
        # Additional sanitization for security
        branch_name = f"auto/{issue['number']}-{slug}"
        return sanitize_branch_name(branch_name)
    
    def generate_issue_context(self, issue: Dict[str, Any]) -> str:
        """Generate comprehensive context information for Claude from a GitHub issue."""
        context_parts = []
        
        # Header
        context_parts.append(f"# Issue #{issue['number']}: {issue['title']}")
        context_parts.append("")
        
        # Metadata
        context_parts.append(f"**Created by:** {issue['user']['login']}")
        context_parts.append(f"**Created at:** {issue['created_at']}")
        
        # Labels
        labels = [label['name'] for label in issue.get('labels', [])]
        if labels:
            context_parts.append(f"**Labels:** {', '.join(labels)}")
        
        context_parts.append("")
        
        # Description
        if issue.get('body'):
            context_parts.append("## Description")
            context_parts.append("")
            context_parts.append(issue['body'])
            context_parts.append("")
        
        # Acceptance criteria
        context_parts.extend([
            "## Acceptance Criteria",
            "",
            "Please implement the feature/fix described above. "
            "Follow the existing code patterns and conventions in the repository. "
            "Write clear, atomic commits with conventional commit messages. "
            "Ensure tests pass if a test command is configured.",
            "",
            f"**Issue URL:** {issue['html_url']}"
        ])
        
        return "\n".join(context_parts)