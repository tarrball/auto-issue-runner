# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Auto Issue Runner is a Node.js automation tool that continuously processes GitHub issues by invoking Claude Code to implement solutions and create pull requests. It uses ES modules and requires Node.js 18+.

## Development Commands

```bash
# Start the runner in production mode
npm start

# Start with file watching for development
npm run dev

# Install dependencies
npm install
```

## Configuration

The application uses environment variables configured in `.env` file:

- Copy `.env.example` to `.env` before running
- Required variables: `GITHUB_PAT`, `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_REPO_URL`
- Optional variables include test/build commands, timeouts, and polling intervals
- Configuration validation happens at startup via `src/config.js`

## Architecture

### Core Components

- **`src/index.js`**: Entry point with signal handlers and startup validation
- **`src/runner.js`**: Main orchestrator (`AutoIssueRunner` class) managing the processing cycle
- **`src/config.js`**: Environment variable management and validation
- **`src/issues.js`**: GitHub issue selection and filtering logic  
- **`src/claude.js`**: Claude Code invocation and context building
- **`src/git.js`**: Git operations (branching, commits, pushing)
- **`src/pr.js`**: Pull request creation and management
- **`src/github.js`**: GitHub API client wrapper
- **`src/lock.js`**: Process locking to prevent concurrent runs

### Processing Flow

1. **Issue Discovery**: Finds eligible issues with required labels, unassigned, oldest first
2. **Branch Creation**: Creates `auto/<issue-number>-<slug>` branches
3. **Claude Invocation**: Runs Claude Code with repository context and issue details
4. **Testing/Building**: Executes configured `TEST_COMMAND` and `BUILD_COMMAND`
5. **Commit & PR**: Creates commits with conventional commit format and opens pull requests

### Error Handling Patterns

- Process locks prevent multiple instances
- Claude timeouts are retried once before skipping
- Failed tests/builds create draft PRs with failure details
- GitHub API rate limiting uses exponential backoff
- Graceful shutdown on SIGINT/SIGTERM with final statistics

## Development Notes

- All modules use ES6 imports/exports
- No test framework is configured - test commands come from environment
- Console output includes emoji indicators and JSON summaries
- Process runs continuously with configurable polling intervals
- Lock files (`.auto-runner.lock`) prevent duplicate execution