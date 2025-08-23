# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Auto Issue Runner is a Python automation tool that continuously processes GitHub issues by invoking Claude Code to implement solutions and create pull requests. It uses modern async/await patterns and requires Python 3.11+.

## Development Commands

```bash
# Setup development environment (one time)
make dev-setup
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package and dependencies
make install

# Run quality checks
make check    # Runs format, lint, typecheck, test

# Individual tools
make format   # black .
make lint     # ruff check . --fix
make typecheck # mypy .
make test     # pytest

# Run the application
make run      # python -m auto_issue_runner.main
```

## Configuration

The application uses environment variables configured in `.env` file:

- Copy `.env.example` to `.env` before running
- Required variables: `GITHUB_PAT`, `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_REPO_URL`, `CLAUDE_WORKING_DIRECTORY`
- Optional variables include test/build commands, timeouts, and polling intervals
- Configuration validation happens at startup via `src/auto_issue_runner/config.py`

## Architecture

### Core Components

- **`src/auto_issue_runner/main.py`**: Entry point with async event loop and startup validation
- **`src/auto_issue_runner/runner.py`**: Main orchestrator (`AutoIssueRunner` class) with async coordination
- **`src/auto_issue_runner/config.py`**: Pydantic-based configuration management and validation
- **`src/auto_issue_runner/issue_selector.py`**: GitHub issue selection with single PR limit
- **`src/auto_issue_runner/claude_handler.py`**: Claude Code subprocess management with proper permissions
- **`src/auto_issue_runner/git_operations.py`**: Git operations with proper working directory
- **`src/auto_issue_runner/pr_manager.py`**: Pull request creation and management
- **`src/auto_issue_runner/github_client.py`**: Async GitHub API client with retry logic
- **`src/auto_issue_runner/process_lock.py`**: Process locking with graceful shutdown
- **`src/auto_issue_runner/validators.py`**: Input validation for security

### Processing Flow

1. **Issue Discovery**: Finds eligible issues with required labels, unassigned, oldest first
2. **Single PR Check**: Only processes issues when NO Claude PRs are open (prevents conflicts)
3. **Branch Creation**: Creates `auto/<issue-number>-<slug>` branches with proper sanitization
4. **Claude Invocation**: Runs Claude with comprehensive context and pre-approved tool permissions
5. **Testing/Building**: Executes configured commands with proper working directory
6. **Commit & PR**: Creates conventional commits and opens pull requests with detailed descriptions

### Error Handling Patterns

- **Async coordination**: Prevents overlapping cycles and race conditions
- **Process locks**: Prevent multiple instances with graceful cleanup
- **Claude timeouts**: Proper subprocess management with configurable timeouts
- **Input validation**: Sanitizes GitHub data to prevent injection attacks
- **GitHub API rate limiting**: Exponential backoff with proper retry logic
- **Graceful shutdown**: Clean shutdown with resource cleanup and final statistics

## Development Notes

- **Modern Python**: Uses async/await, type hints, and Pydantic for validation
- **Quality tooling**: Black, Ruff, MyPy with strict configuration
- **Testing**: Pytest with async support and coverage reporting
- **Security**: Input validation, subprocess security, no shell injection
- **Observability**: Structured logging with colors and emoji indicators
- **Type safety**: Full type annotations with `py.typed` marker
- **Documentation**: Comprehensive docstrings and README

## Important Instruction Reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.