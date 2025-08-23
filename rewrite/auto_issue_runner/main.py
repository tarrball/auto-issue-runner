"""Main entry point for the auto issue runner."""

import asyncio
import sys
from pathlib import Path

from .config import Config, load_config, print_config_summary
from .logging_config import setup_logging, get_logger
from .runner import AutoIssueRunner

logger = get_logger(__name__)


async def main_async() -> None:
    """Async main function."""
    try:
        # Load configuration
        config = load_config()
        
        # Set up logging
        setup_logging(level="INFO")
        
        # Print configuration summary
        print_config_summary(config)
        
        # Create and start runner
        runner = AutoIssueRunner(config)
        await runner.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    # Ensure we're using the right event loop policy on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass  # Already handled in main_async
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()