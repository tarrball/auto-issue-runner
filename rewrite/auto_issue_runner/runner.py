"""Main runner orchestrating the auto issue processing cycle."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .config import Config
from .github_client import GitHubClient
from .issue_selector import IssueSelector
from .claude_handler import ClaudeHandler
from .git_operations import GitOperations
from .pr_manager import PRManager
from .process_lock import ProcessLock

logger = logging.getLogger(__name__)


@dataclass
class CycleResult:
    """Result of a single processing cycle."""
    cycle_id: int
    start_time: float
    end_time: float = 0
    issue: Optional[int] = None
    branch: Optional[str] = None
    pr_number: Optional[int] = None
    status: str = 'UNKNOWN'
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> int:
        return int((self.end_time - self.start_time) * 1000)


class AutoIssueRunner:
    """Main orchestrator for the auto issue processing system."""
    
    def __init__(self, config: Config):
        self.config = config
        self.is_running = False
        self.cycle_count = 0
        self.results: List[CycleResult] = []
        self._polling_task: Optional[asyncio.Task] = None
        self._current_cycle_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Initialize components
        self.process_lock = ProcessLock(config.claude_working_directory)
        self.github_client: Optional[GitHubClient] = None
        self.issue_selector: Optional[IssueSelector] = None
        self.claude_handler: Optional[ClaudeHandler] = None
        self.git_ops: Optional[GitOperations] = None
        self.pr_manager: Optional[PRManager] = None
    
    async def start(self) -> None:
        """Start the auto issue runner."""
        try:
            logger.info("🚀 Starting Auto Issue Runner...")
            logger.info(f"   Repository: {self.config.github_owner}/{self.config.github_repo}")
            logger.info(f"   Working Directory: {self.config.claude_working_directory}")
            logger.info(f"   Polling Interval: {self.config.polling_interval_ms / 1000}s")
            
            # Acquire process lock
            await self.process_lock.acquire()
            self.process_lock.setup_graceful_shutdown(self)
            
            # Initialize components
            await self._initialize_components()
            
            self.is_running = True
            
            # Run initial cycle
            await self._run_initial_cycle()
            
            # Start polling loop
            if self.is_running:
                await self._start_polling()
            
        except Exception as e:
            logger.error(f"❌ Failed to start runner: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the runner gracefully."""
        logger.info("🛑 Stopping Auto Issue Runner...")
        self.is_running = False
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel polling task
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        # Wait for current cycle to complete
        if self._current_cycle_task and not self._current_cycle_task.done():
            logger.info("⏳ Waiting for current cycle to complete...")
            try:
                await asyncio.wait_for(self._current_cycle_task, timeout=30)
            except asyncio.TimeoutError:
                logger.warning("⚠️  Current cycle didn't complete in time, cancelling...")
                self._current_cycle_task.cancel()
        
        # Cleanup
        await self._cleanup()
        
        # Print final statistics
        self._print_final_statistics()
        
        logger.info("✅ Auto Issue Runner stopped")
    
    async def _initialize_components(self) -> None:
        """Initialize all component instances."""
        self.github_client = GitHubClient(self.config)
        await self.github_client.__aenter__()  # Initialize session
        
        self.issue_selector = IssueSelector(self.github_client)
        self.claude_handler = ClaudeHandler(self.config, self.github_client)
        self.git_ops = GitOperations(self.config)
        self.pr_manager = PRManager(self.github_client)
    
    async def _run_initial_cycle(self) -> None:
        """Run the first cycle immediately after startup."""
        logger.info("🎬 Running initial cycle...")
        await self._run_cycle()
    
    async def _start_polling(self) -> None:
        """Start the polling loop."""
        polling_interval = self.config.polling_interval_ms / 1000
        logger.info(f"🔄 Starting polling every {polling_interval}s...")
        
        self._polling_task = asyncio.create_task(self._polling_loop())
        
        try:
            await self._polling_task
        except asyncio.CancelledError:
            logger.info("🛑 Polling cancelled")
    
    async def _polling_loop(self) -> None:
        """Main polling loop that runs cycles at intervals."""
        polling_interval = self.config.polling_interval_ms / 1000
        
        while self.is_running:
            try:
                # Wait for the next cycle or shutdown
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=polling_interval
                )
                break  # Shutdown was signaled
            except asyncio.TimeoutError:
                # Timeout is expected - time for next cycle
                if self.is_running:
                    await self._run_cycle()
    
    async def _run_cycle(self) -> None:
        """Execute one complete cycle: find issue → implement → test → commit → create PR."""
        if not self.is_running:
            return
        
        self.cycle_count += 1
        result = CycleResult(
            cycle_id=self.cycle_count,
            start_time=time.time()
        )
        
        logger.info(f"🔄 Starting cycle #{self.cycle_count}")
        
        # Prevent overlapping cycles
        if self._current_cycle_task and not self._current_cycle_task.done():
            logger.warning("⚠️  Previous cycle still running, skipping this cycle")
            return
        
        self._current_cycle_task = asyncio.create_task(self._execute_cycle(result))
        
        try:
            await self._current_cycle_task
        except Exception as e:
            logger.error(f"❌ Cycle #{self.cycle_count} failed: {e}")
            result.error = str(e)
            result.status = 'ERROR'
        finally:
            result.end_time = time.time()
            self.results.append(result)
            self._log_cycle_result(result)
            self._current_cycle_task = None
    
    async def _execute_cycle(self, result: CycleResult) -> None:
        """Execute the actual cycle logic."""
        try:
            # Find eligible issue
            issue = await self.issue_selector.find_eligible_issue()
            
            if not issue:
                result.status = 'NO_ISSUES'
                logger.info("✅ No eligible issues found")
                return
            
            result.issue = issue['number']
            branch_name = self.issue_selector.generate_branch_name(issue)
            result.branch = branch_name
            
            logger.info(f"🎯 Processing issue #{issue['number']}: {issue['title']}")
            logger.info(f"🌿 Branch: {branch_name}")
            
            # Git setup
            await self.git_ops.sync_with_default()
            await self.git_ops.create_and_checkout_branch(branch_name)
            
            # Generate contexts and prompt
            issue_context = self.issue_selector.generate_issue_context(issue)
            repo_context = await self.claude_handler.generate_repo_context()
            issue['context'] = issue_context
            
            prompt_path = await self.claude_handler.create_prompt_file(issue, repo_context)
            
            # Invoke Claude
            try:
                await self.claude_handler.invoke_claude(prompt_path, max_retries=1)
                
                # Run tests and build
                tests_pass = await self.git_ops.run_tests()
                build_pass = await self.git_ops.run_build()
                
                if not tests_pass or not build_pass:
                    raise Exception('Tests or build failed after Claude implementation')
                
                # Clean up temporary files before git operations
                await self.claude_handler.cleanup()
                
                # Check for changes and commit
                if await self.git_ops.has_changes():
                    commit_message = self.git_ops.generate_commit_message(issue)
                    await self.git_ops.add_all_changes()
                    await self.git_ops.create_commit(commit_message)
                    await self.git_ops.push_branch(branch_name)
                    
                    # Create PR
                    pr = await self.pr_manager.create_pull_request(issue, branch_name)
                    result.pr_number = pr['number']
                    result.status = 'SUCCESS'
                    
                    logger.info(f"✅ Successfully processed issue #{issue['number']}")
                    logger.info(f"📝 PR created: {pr['html_url']}")
                else:
                    result.status = 'NO_CHANGES'
                    logger.info(f"⚠️  No changes made for issue #{issue['number']}")
                
            except Exception as e:
                # Create draft PR with failure details if there are changes
                await self.claude_handler.cleanup()
                
                if await self.git_ops.has_changes():
                    logger.info("📝 Creating draft PR with failure details...")
                    commit_message = f"WIP: Failed implementation for #{issue['number']}\n\nError: {str(e)}"
                    await self.git_ops.add_all_changes()
                    await self.git_ops.create_commit(commit_message)
                    await self.git_ops.push_branch(branch_name)
                    
                    # Note: GitHub API doesn't directly support draft PRs in this version
                    # The PR will be created normally but marked with failure details
                    
                result.status = 'CLAUDE_FAILED'
                result.error = str(e)
                raise
                
        except Exception as e:
            logger.error(f"❌ Cycle execution failed: {e}")
            result.error = str(e)
            if not result.status or result.status == 'UNKNOWN':
                result.status = 'ERROR'
            raise
    
    def _log_cycle_result(self, result: CycleResult) -> None:
        """Log the result of a cycle."""
        duration = result.duration_ms / 1000
        
        if result.status == 'SUCCESS':
            logger.info(f"✅ Cycle #{result.cycle_id} completed in {duration:.1f}s - Issue #{result.issue} -> PR #{result.pr_number}")
        elif result.status == 'NO_ISSUES':
            logger.info(f"📭 Cycle #{result.cycle_id} completed in {duration:.1f}s - No eligible issues")
        elif result.status == 'NO_CHANGES':
            logger.info(f"⚠️  Cycle #{result.cycle_id} completed in {duration:.1f}s - No changes made for issue #{result.issue}")
        else:
            logger.error(f"❌ Cycle #{result.cycle_id} failed in {duration:.1f}s - Status: {result.status}")
    
    def _print_final_statistics(self) -> None:
        """Print final statistics about the runner's performance."""
        if not self.results:
            logger.info("📊 No cycles completed")
            return
        
        total_cycles = len(self.results)
        successful = len([r for r in self.results if r.status == 'SUCCESS'])
        failed = len([r for r in self.results if r.status in ['ERROR', 'CLAUDE_FAILED']])
        no_issues = len([r for r in self.results if r.status == 'NO_ISSUES'])
        no_changes = len([r for r in self.results if r.status == 'NO_CHANGES'])
        
        avg_duration = sum(r.duration_ms for r in self.results) / total_cycles / 1000
        
        logger.info("📊 Final Statistics:")
        logger.info(f"   Total Cycles: {total_cycles}")
        logger.info(f"   Successful: {successful}")
        logger.info(f"   Failed: {failed}")
        logger.info(f"   No Issues: {no_issues}")
        logger.info(f"   No Changes: {no_changes}")
        logger.info(f"   Average Duration: {avg_duration:.1f}s")
        
        if successful > 0:
            logger.info(f"   Success Rate: {successful/total_cycles*100:.1f}%")
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        logger.info("🧹 Cleaning up resources...")
        
        try:
            if self.claude_handler:
                await self.claude_handler.cleanup_all()
        except Exception as e:
            logger.debug(f"Error cleaning up Claude handler: {e}")
        
        try:
            await self.process_lock.release()
        except Exception as e:
            logger.debug(f"Error releasing process lock: {e}")
        
        try:
            if self.github_client:
                await self.github_client.__aexit__(None, None, None)
        except Exception as e:
            logger.debug(f"Error closing GitHub client: {e}")