"""GitHub API client using aiohttp."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

import aiohttp

from .config import Config

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Exception raised for GitHub API errors."""
    pass


class GitHubClient:
    """Async GitHub API client with retry logic."""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'Authorization': f'token {config.github_pat}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'auto-issue-runner/2.0.0'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with exponential backoff retry."""
        if not self.session:
            raise RuntimeError("GitHubClient not initialized. Use as async context manager.")
        
        for attempt in range(max_retries):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 403:
                        # Rate limit handling
                        reset_time = response.headers.get('X-RateLimit-Reset')
                        if reset_time:
                            wait_time = min(int(reset_time) - asyncio.get_event_loop().time(), 3600)
                            logger.warning(f"Rate limited. Waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                    elif response.status in (404, 422):
                        # Client errors that shouldn't be retried
                        error_body = await response.text()
                        raise GitHubAPIError(f"GitHub API error {response.status}: {error_body}")
                    
                    # Server errors - retry with backoff
                    if response.status >= 500 and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1.0  # Exponential backoff
                        logger.warning(f"Server error {response.status}, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    # Final attempt failed
                    error_body = await response.text()
                    raise GitHubAPIError(f"GitHub API error {response.status}: {error_body}")
                    
            except aiohttp.ClientError as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1.0
                    logger.warning(f"Client error {e}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise GitHubAPIError(f"Client error: {e}")
        
        raise GitHubAPIError("Max retries exceeded")
    
    async def search_eligible_issues(self) -> List[Dict[str, Any]]:
        """Search for eligible issues using GitHub Search API."""
        query_parts = [
            f"repo:{self.config.github_owner}/{self.config.github_repo}",
            "is:issue",
            "is:open",
            "no:assignee",
            f"label:{self.config.issue_label}",
            f"label:{self.config.claude_help_wanted_label}"
        ]
        
        query = " ".join(query_parts)
        params = {
            'q': query,
            'sort': 'created',
            'order': 'asc',
            'per_page': 100
        }
        
        url = f"{self.base_url}/search/issues?{urlencode(params)}"
        result = await self._make_request('GET', url)
        
        logger.info(f"Found {result.get('total_count', 0)} eligible issues")
        return result.get('items', [])
    
    async def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """Get detailed issue information."""
        url = f"{self.base_url}/repos/{self.config.github_owner}/{self.config.github_repo}/issues/{issue_number}"
        return await self._make_request('GET', url)
    
    async def get_open_pull_requests(self) -> List[Dict[str, Any]]:
        """Get all open pull requests created by this bot."""
        params = {
            'state': 'open',
            'per_page': 100
        }
        
        url = f"{self.base_url}/repos/{self.config.github_owner}/{self.config.github_repo}/pulls?{urlencode(params)}"
        result = await self._make_request('GET', url)
        
        # Filter to only include PRs with auto/ branch prefix
        auto_prs = [pr for pr in result if pr['head']['ref'].startswith('auto/')]
        
        logger.info(f"Found {len(auto_prs)} open auto/ PRs")
        return auto_prs
    
    async def get_recent_commits(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent commits from the default branch."""
        params = {
            'sha': self.config.github_default_branch,
            'per_page': count
        }
        
        url = f"{self.base_url}/repos/{self.config.github_owner}/{self.config.github_repo}/commits?{urlencode(params)}"
        return await self._make_request('GET', url)
    
    async def get_repo_content(self, path: str) -> Optional[Dict[str, Any]]:
        """Get content of a file from the repository."""
        try:
            url = f"{self.base_url}/repos/{self.config.github_owner}/{self.config.github_repo}/contents/{path}"
            return await self._make_request('GET', url)
        except GitHubAPIError as e:
            if "404" in str(e):
                return None
            raise
    
    async def create_pull_request(
        self, 
        title: str, 
        body: str, 
        head: str, 
        base: str = None
    ) -> Dict[str, Any]:
        """Create a new pull request."""
        if base is None:
            base = self.config.github_default_branch
        
        data = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        
        url = f"{self.base_url}/repos/{self.config.github_owner}/{self.config.github_repo}/pulls"
        return await self._make_request('POST', url, json=data)