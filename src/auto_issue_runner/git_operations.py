"""Git operations for the auto issue runner."""

import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import Config

logger = logging.getLogger(__name__)


class GitOperations:
    """Handles all git operations for the auto issue runner."""
    
    def __init__(self, config: Config):
        self.config = config
        self.working_dir = Path(config.claude_working_directory)
    
    async def _run_git_command(self, args: List[str]) -> Dict[str, Any]:
        """Execute a git command with the given arguments."""
        cmd_args = ['git'] + args
        
        logger.debug(f"Running: {' '.join(cmd_args)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            cwd=self.working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        result = {
            'stdout': stdout.decode('utf-8', errors='replace').strip(),
            'stderr': stderr.decode('utf-8', errors='replace').strip(),
            'exit_code': process.returncode
        }
        
        if process.returncode != 0:
            error_msg = result['stderr'] or result['stdout']
            raise Exception(f"Git command failed (exit {process.returncode}): {error_msg}")
        
        return result
    
    async def _run_shell_command(self, command: str) -> Dict[str, Any]:
        """Execute a shell command (used for test and build commands)."""
        logger.debug(f"Running shell command: {command}")
        
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=self.working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        stdout, _ = await process.communicate()
        
        result = {
            'stdout': stdout.decode('utf-8', errors='replace').strip(),
            'exit_code': process.returncode
        }
        
        if process.returncode != 0:
            raise Exception(f"Command failed with exit code {process.returncode}: {command}")
        
        return result
    
    async def sync_with_default(self) -> None:
        """Sync the local repository with the default branch."""
        logger.info(f"🔄 Syncing with {self.config.github_default_branch} branch...")
        
        try:
            await self._run_git_command(['fetch', 'origin'])
            await self._run_git_command(['checkout', self.config.github_default_branch])
            await self._run_git_command(['pull', 'origin', self.config.github_default_branch])
            logger.info("✅ Successfully synced with default branch")
        except Exception as e:
            logger.error(f"❌ Failed to sync with default branch: {e}")
            raise
    
    async def create_and_checkout_branch(self, branch_name: str) -> None:
        """Create and check out a new branch, or check out if it already exists."""
        logger.info(f"🌿 Creating and checking out branch: {branch_name}")
        
        try:
            await self._run_git_command(['checkout', '-b', branch_name])
            logger.info(f"✅ Successfully created branch: {branch_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"📌 Branch {branch_name} already exists, checking out...")
                await self._run_git_command(['checkout', branch_name])
            else:
                raise
    
    async def has_changes(self) -> bool:
        """Check if there are any uncommitted changes in the repository."""
        try:
            result = await self._run_git_command(['status', '--porcelain'])
            
            if result['stdout']:
                logger.info("📝 Detected changes:")
                for line in result['stdout'].split('\n'):
                    if line.strip():
                        logger.info(f"   {line}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"❌ Failed to check git status: {e}")
            return False
    
    async def add_all_changes(self) -> None:
        """Add all changes to the git staging area."""
        logger.info("📦 Adding all changes to staging...")
        try:
            await self._run_git_command(['add', '.'])
            logger.info("✅ Successfully added all changes")
        except Exception as e:
            logger.error(f"❌ Failed to add changes: {e}")
            raise
    
    async def create_commit(self, message: str) -> None:
        """Create a git commit with the given message."""
        logger.info("💾 Creating commit...")
        try:
            await self._run_git_command(['commit', '-m', message])
            logger.info(f"✅ Successfully created commit: {message.split()[0]}...")
        except Exception as e:
            logger.error(f"❌ Failed to create commit: {e}")
            raise
    
    async def push_branch(self, branch_name: str) -> None:
        """Push a branch to the remote origin repository."""
        logger.info(f"🚀 Pushing branch {branch_name} to origin...")
        try:
            await self._run_git_command(['push', '-u', 'origin', branch_name])
            logger.info("✅ Successfully pushed branch to origin")
        except Exception as e:
            logger.error(f"❌ Failed to push branch: {e}")
            raise
    
    async def run_tests(self) -> bool:
        """Run the configured test command if available."""
        if not self.config.test_command:
            logger.info("📋 No test command configured, skipping tests")
            return True
        
        logger.info(f"🧪 Running tests: {self.config.test_command}")
        try:
            await self._run_shell_command(self.config.test_command)
            logger.info("✅ Tests passed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Tests failed: {e}")
            return False
    
    async def run_build(self) -> bool:
        """Run the configured build command if available."""
        if not self.config.build_command:
            logger.info("📋 No build command configured, skipping build")
            return True
        
        logger.info(f"🔨 Running build: {self.config.build_command}")
        try:
            await self._run_shell_command(self.config.build_command)
            logger.info("✅ Build completed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Build failed: {e}")
            return False
    
    def generate_commit_message(self, issue: Dict[str, Any]) -> str:
        """Generate a conventional commit message from a GitHub issue."""
        title = issue['title']
        if len(title) > 50:
            title = title[:47] + '...'
        
        commit_type = self._infer_commit_type(issue)
        scope = self._infer_commit_scope(issue)
        
        # Build the commit header
        message_parts = [commit_type]
        if scope:
            message_parts[0] += f"({scope})"
        message_parts[0] += f": {title}"
        
        # Add the body
        message_parts.extend([
            "",
            f"Closes #{issue['number']}"
        ])
        
        # Add issue body preview if available
        body = issue.get('body', '').strip()
        if body:
            body_preview = body.split('\n')[0]
            if body_preview and body_preview != title:
                message_parts.extend([
                    "",
                    body_preview
                ])
        
        # Add signature
        message_parts.extend([
            "",
            "🤖 Generated with Claude Code"
        ])
        
        return "\n".join(message_parts)
    
    def _infer_commit_type(self, issue: Dict[str, Any]) -> str:
        """Infer the conventional commit type from issue content."""
        title = issue['title'].lower()
        body = (issue.get('body') or '').lower()
        content = f"{title} {body}"
        
        if any(keyword in content for keyword in ['fix', 'bug', 'error', 'issue']):
            return 'fix'
        if any(keyword in content for keyword in ['test', 'spec', 'testing']):
            return 'test'
        if any(keyword in content for keyword in ['doc', 'readme', 'documentation']):
            return 'docs'
        if any(keyword in content for keyword in ['refactor', 'cleanup', 'clean up']):
            return 'refactor'
        if any(keyword in content for keyword in ['perf', 'performance', 'optimize']):
            return 'perf'
        
        return 'feat'
    
    def _infer_commit_scope(self, issue: Dict[str, Any]) -> Optional[str]:
        """Infer the conventional commit scope from issue labels and title."""
        # Extract labels
        labels = {label['name'].lower() for label in issue.get('labels', [])}
        title = issue['title'].lower()
        
        # Scope mapping
        scope_map = {
            'ui': 'ui',
            'api': 'api', 
            'auth': 'auth',
            'database': 'db',
            'db': 'db',
            'config': 'config',
            'deps': 'deps',
            'dependencies': 'deps',
            'frontend': 'ui',
            'backend': 'api'
        }
        
        # Check labels first (more reliable)
        for label in labels:
            if label in scope_map:
                return scope_map[label]
        
        # Fallback to checking title content
        for keyword, scope in scope_map.items():
            if keyword in title:
                return scope
        
        return None