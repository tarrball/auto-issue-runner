"""Claude Code invocation and context generation."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import base64

import aiofiles

from .config import Config
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class ClaudeHandler:
    """Handles Claude Code invocation and context generation."""
    
    # Claude allowed tools configuration
    ALLOWED_TOOLS = [
        "Read(**)",
        "Edit(**)",
        "Bash(git:*,npm:*,ng:*,yarn:*)",
        "Task",
        "WebFetch", 
        "WebSearch",
        "TodoRead",
        "TodoWrite",
        "NotebookRead",
        "NotebookEdit",
        "Batch",
    ]
    
    def __init__(self, config: Config, github_client: GitHubClient):
        self.config = config
        self.github_client = github_client
        self.working_dir = Path(config.claude_working_directory)
    
    async def generate_repo_context(self) -> str:
        """Generate repository context by fetching README, CONTRIBUTING, and recent commits."""
        context_parts = []
        
        # Try to get README.md
        try:
            readme = await self.github_client.get_repo_content('README.md')
            if readme and readme.get('content'):
                readme_content = base64.b64decode(readme['content']).decode('utf-8')
                context_parts.extend([
                    "## Repository README",
                    "",
                    readme_content,
                    ""
                ])
        except Exception as e:
            logger.debug(f"No README.md found or accessible: {e}")
        
        # Try to get CONTRIBUTING.md
        try:
            contributing = await self.github_client.get_repo_content('CONTRIBUTING.md')
            if contributing and contributing.get('content'):
                contrib_content = base64.b64decode(contributing['content']).decode('utf-8')
                context_parts.extend([
                    "## Contributing Guidelines",
                    "",
                    contrib_content,
                    ""
                ])
        except Exception as e:
            logger.debug(f"No CONTRIBUTING.md found or accessible: {e}")
        
        # Get recent commits
        try:
            recent_commits = await self.github_client.get_recent_commits(5)
            if recent_commits:
                context_parts.extend([
                    "## Recent Commits",
                    ""
                ])
                for commit in recent_commits:
                    sha = commit['sha'][:7]
                    message = commit['commit']['message'].split('\n')[0]
                    context_parts.append(f"- {sha}: {message}")
                context_parts.append("")
        except Exception as e:
            logger.debug(f"Could not fetch recent commits: {e}")
        
        return "\n".join(context_parts)
    
    async def create_prompt_file(self, issue: Dict[str, Any], repo_context: str) -> Path:
        """Create a comprehensive prompt file for Claude with issue and repository context."""
        prompt_parts = [
            "You are working on a GitHub repository issue. Please implement the requested changes following these guidelines:",
            "",
            repo_context,
            "",
            issue.get('context', ''),
            "",
            "## Implementation Guidelines",
            "",
            "1. **Code Quality**: Follow existing patterns and conventions in the codebase",
            "2. **Commit Standards**: Make atomic commits with conventional commit messages",
            "3. **Testing**: Run tests if configured, fix any failures",
            "4. **Documentation**: Update relevant documentation if needed",
            "5. **Error Handling**: Include appropriate error handling and edge cases",
            "",
            "## Commands Available",
            ""
        ]
        
        # Add available commands
        if self.config.test_command:
            prompt_parts.append(f"- Test command: {self.config.test_command}")
        else:
            prompt_parts.append("- No test command configured")
            
        if self.config.build_command:
            prompt_parts.append(f"- Build command: {self.config.build_command}")
        else:
            prompt_parts.append("- No build command configured")
        
        prompt_parts.extend([
            "",
            "## Next Steps",
            "",
            "Please implement the changes described in the issue. Once complete:",
            "1. Run any configured test/build commands",
            "2. Make atomic, well-described commits",
            "3. The system will automatically create a pull request",
            "",
            "Focus on implementing a complete, working solution that addresses all aspects of the issue."
        ])
        
        prompt_content = "\n".join(prompt_parts)
        prompt_path = self.working_dir / "issue_prompt.md"
        
        async with aiofiles.open(prompt_path, 'w', encoding='utf-8') as f:
            await f.write(prompt_content)
        
        logger.debug(f"Created prompt file: {prompt_path}")
        return prompt_path
    
    async def invoke_claude(self, prompt_path: Path, max_retries: int = 1) -> Dict[str, Any]:
        """Invoke Claude Code with retry logic."""
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"🤖 Invoking Claude (attempt {attempt + 1}/{max_retries + 1})...")
                
                result = await self._run_claude_command(prompt_path)
                
                logger.info("✅ Claude Code completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"❌ Claude Code attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries:
                    logger.info("⏳ Retrying in 10 seconds...")
                    await asyncio.sleep(10)
                    continue
                
                raise Exception(f"Claude Code failed after {max_retries + 1} attempts: {e}")
    
    async def _run_claude_command(self, prompt_path: Path) -> Dict[str, Any]:
        """Execute the Claude Code command with timeout handling."""
        # Read prompt content
        async with aiofiles.open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_content = await f.read()
        
        # Create debug prompt file for inspection
        debug_path = self.working_dir / "debug_claude_prompt.md"
        async with aiofiles.open(debug_path, 'w', encoding='utf-8') as f:
            await f.write(prompt_content)
        
        logger.info(f"📝 Prompt written to {debug_path}")
        
        # Build Claude command
        cmd_args = [
            'claude',
            '--permission-mode', 'acceptEdits',
            '--allowed-tools', ','.join(self.ALLOWED_TOOLS),
            '--print',
            prompt_content
        ]
        
        logger.info("🚀 Executing Claude Code...")
        
        # Run Claude with proper working directory
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            cwd=self.working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Wait for completion with timeout
            timeout_seconds = self.config.claude_timeout_ms / 1000
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds
            )
            
            exit_code = process.returncode
            
            if exit_code == 0:
                # Clean up debug file on success
                try:
                    await aiofiles.os.remove(debug_path)
                    logger.debug("🧹 Cleaned up debug prompt file")
                except Exception:
                    pass  # Ignore cleanup errors
                
                return {
                    'stdout': stdout.decode('utf-8', errors='replace'),
                    'stderr': stderr.decode('utf-8', errors='replace'),
                    'exit_code': exit_code
                }
            else:
                stderr_text = stderr.decode('utf-8', errors='replace')
                raise Exception(f"Claude exited with code {exit_code}: {stderr_text}")
                
        except asyncio.TimeoutError:
            # Kill the process if it times out
            process.kill()
            await process.wait()
            raise Exception(f"Claude Code timed out after {timeout_seconds}s")
    
    async def cleanup(self) -> None:
        """Clean up temporary files created during Claude invocation."""
        files_to_clean = [
            self.working_dir / "issue_prompt.md",
            self.working_dir / "debug_claude_prompt.md"
        ]
        
        for file_path in files_to_clean:
            try:
                if file_path.exists():
                    await aiofiles.os.remove(file_path)
                    logger.debug(f"🧹 Cleaned up: {file_path.name}")
            except Exception as e:
                logger.debug(f"Could not clean up {file_path}: {e}")
    
    async def cleanup_all(self) -> None:
        """Clean up all auto-runner artifacts from the working directory."""
        await self.cleanup()
        
        # Also clean up lock file
        lock_path = self.working_dir / ".auto-runner.lock"
        try:
            if lock_path.exists():
                await aiofiles.os.remove(lock_path)
                logger.debug("🧹 Cleaned up: .auto-runner.lock")
        except Exception as e:
            logger.debug(f"Could not clean up lock file: {e}")