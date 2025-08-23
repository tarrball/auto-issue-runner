"""Process locking to prevent multiple runner instances."""

import asyncio
import logging
import os
import signal
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import aiofiles

if TYPE_CHECKING:
    from .runner import AutoIssueRunner

logger = logging.getLogger(__name__)


class ProcessLock:
    """Manages process locking to prevent multiple runner instances."""
    
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.lock_file = working_dir / ".auto-runner.lock"
        self.lock_acquired = False
        self.pid = os.getpid()
        self._shutdown_handlers_registered = False
    
    async def is_process_running(self, pid: int) -> bool:
        """Check if a process with the given PID is running."""
        try:
            os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
            return True
        except (OSError, ProcessLookupError):
            return False
    
    async def acquire(self) -> None:
        """Acquire the process lock."""
        try:
            # Check if lock file exists
            if self.lock_file.exists():
                async with aiofiles.open(self.lock_file, 'r') as f:
                    content = await f.read()
                    existing_pid = int(content.strip())
                
                if await self.is_process_running(existing_pid):
                    raise Exception(f"Auto runner already running with PID {existing_pid}")
                
                logger.info(f"🧹 Cleaning up stale lock file from PID {existing_pid}")
                await aiofiles.os.remove(self.lock_file)
        
        except FileNotFoundError:
            pass  # Lock file doesn't exist, which is fine
        except ValueError:
            logger.warning("⚠️  Invalid lock file content, removing...")
            await aiofiles.os.remove(self.lock_file)
        
        # Create new lock file
        async with aiofiles.open(self.lock_file, 'w') as f:
            await f.write(str(self.pid))
        
        self.lock_acquired = True
        logger.info(f"🔒 Lock acquired with PID {self.pid}")
    
    async def release(self) -> None:
        """Release the process lock."""
        if not self.lock_acquired:
            return
        
        try:
            if self.lock_file.exists():
                await aiofiles.os.remove(self.lock_file)
            self.lock_acquired = False
            logger.info(f"🔓 Lock released for PID {self.pid}")
        except Exception as e:
            logger.error(f"❌ Failed to release lock: {e}")
    
    def setup_graceful_shutdown(self, runner: Optional['AutoIssueRunner'] = None) -> None:
        """Set up graceful shutdown handlers."""
        if self._shutdown_handlers_registered:
            return
        
        def signal_handler(signum, frame):
            logger.info(f"\n🛑 Received signal {signum}, shutting down gracefully...")
            
            # Create a new event loop if we're not in one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            async def cleanup():
                if runner:
                    await runner.stop()
                else:
                    await self.release()
            
            if loop.is_running():
                # If we're in an async context, schedule the cleanup
                asyncio.create_task(cleanup())
            else:
                # If we're not in an async context, run it
                loop.run_until_complete(cleanup())
                loop.close()
            
            os._exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        self._shutdown_handlers_registered = True
        logger.debug("📡 Graceful shutdown handlers registered")