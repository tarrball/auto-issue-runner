# Auto Next Issue Runner

A Node.js automation tool that continuously works through GitHub issues by invoking Claude Code to implement solutions and create pull requests.

## Features

- 🔄 Continuously polls for eligible GitHub issues
- 🤖 Uses Claude Code to implement solutions
- 🌟 Creates well-formatted pull requests automatically
- 🔒 Process locking to prevent multiple instances
- ⚡ Rate limiting and retry logic for GitHub API
- 📊 Comprehensive logging and statistics
- 🛡️ Robust error handling and graceful shutdown

## Prerequisites

- Node.js 18.0.0 or higher
- Claude Code CLI installed and accessible in PATH
- Git configured with appropriate credentials
- GitHub Personal Access Token with required permissions

## Installation

1. Clone or download this project
2. Install dependencies:
   ```bash
   npm install
   ```

3. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

4. Configure your environment variables (see Configuration section)

## Configuration

Create a `.env` file with the following variables:

```env
# GitHub Configuration (Required)
GITHUB_PAT=ghp_your_personal_access_token_here
GITHUB_OWNER=your-github-username
GITHUB_REPO=your-repository-name
GITHUB_REPO_URL=https://github.com/your-username/your-repo.git
GITHUB_DEFAULT_BRANCH=main

# Issue Labels (Optional)
ISSUE_LABEL=auto
CLAUDE_HELP_WANTED_LABEL=claude-help-wanted

# Commands (Optional)
TEST_COMMAND=npm test
BUILD_COMMAND=npm run build

# Timeouts (Optional)
CLAUDE_TIMEOUT_MS=300000
POLLING_INTERVAL_MS=180000
```

### GitHub PAT Permissions

Your Personal Access Token should have the following permissions for the target repository:

- **Contents**: Read and Write
- **Pull requests**: Read and Write  
- **Issues**: Read and Write
- **Metadata**: Read

## Issue Selection Rules

The runner will process issues that meet ALL of the following criteria:

- ✅ Open state
- ✅ Has both required labels (`ISSUE_LABEL` AND `CLAUDE_HELP_WANTED_LABEL`)
- ✅ Unassigned
- ✅ No existing open pull request from this bot
- ✅ Oldest first (FIFO processing)

## Usage

### Start the Runner

```bash
npm start
```

The runner will:
1. Validate configuration
2. Acquire a process lock
3. Run an initial cycle
4. Start polling at the configured interval

### Development Mode

```bash
npm run dev
```

Starts the runner with file watching for development.

### Stop the Runner

Use `Ctrl+C` (SIGINT) for graceful shutdown. The runner will:
- Complete the current cycle
- Release the process lock
- Display final statistics
- Clean up temporary files

## How It Works

### Workflow Overview

1. **Issue Discovery**: Searches for eligible issues using GitHub Search API
2. **Branch Creation**: Creates a new branch with pattern `auto/<issue-number>-<slug>`
3. **Context Generation**: Builds comprehensive context from issue details and repository
4. **Claude Invocation**: Runs Claude Code with detailed prompts and repository context
5. **Testing & Building**: Runs configured test and build commands
6. **Commit Creation**: Creates atomic commits with conventional commit messages
7. **Pull Request**: Opens a PR with detailed description and closes the issue

### Error Handling

- **Claude Timeouts**: Retries once, then skips issue
- **Test/Build Failures**: Creates draft PR with failure details
- **GitHub API Limits**: Implements exponential backoff
- **Process Crashes**: Lock file prevents duplicate runs

### Commit Quality

All commits follow these standards:
- **Conventional Commits**: `type(scope): description`
- **Atomic Changes**: Each commit represents one logical change  
- **Descriptive Messages**: Include the "why" not just the "what"
- **Issue References**: Include `Closes #123` in commit body

## Output & Monitoring

### Console Output

The runner provides detailed console logs for each step:

```
🚀 Starting Auto Issue Runner...
Repository: username/repo-name
Polling interval: 180s
✅ Configuration valid
🔒 Lock acquired with PID 12345
=== Starting new cycle at 2024-01-15T10:30:00.000Z ===
📝 Selected issue #42: Add user authentication
🌿 Creating branch: auto/42-add-user-authentication
🤖 Invoking Claude Code...
✅ Claude Code completed successfully
🧪 Running tests: npm test
🏗️  Running build: npm run build
📤 Pushing branch to origin...
📝 PR created: https://github.com/user/repo/pull/123
✅ Successfully processed issue #42
```

### JSON Output

Each cycle produces a JSON summary:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "issue": 42,
  "branch": "auto/42-add-user-authentication", 
  "pr_number": 123,
  "status": "SUCCESS",
  "duration_ms": 45000
}
```

### Status Values

- `SUCCESS`: Issue implemented and PR created
- `PARTIAL`: Partial work committed as draft PR  
- `FAILED`: Implementation failed, no changes
- `NO_CHANGES`: Claude ran but made no changes
- `NO_ISSUES`: No eligible issues found
- `ERROR`: System error during processing

## Troubleshooting

### Common Issues

**Lock file exists**
```
Error: Auto runner already running with PID 12345
```
- Check if another instance is running: `ps aux | grep node`
- Remove stale lock: `rm .auto-runner.lock`

**GitHub API rate limits**
```
Rate limited, waiting 60000ms before retry 1/3
```
- Normal behavior, the runner will wait and retry
- Consider reducing polling frequency

**Claude Code timeouts**
```
Claude Code failed after 2 attempts: timeout
```
- Increase `CLAUDE_TIMEOUT_MS` in .env
- Simplify issue descriptions
- Check Claude Code is properly installed

**Missing environment variables**
```
Required environment variable GITHUB_PAT is not set
```
- Ensure .env file exists and is configured
- Verify all required variables are set

### Debug Mode

Set environment variable for verbose logging:
```bash
DEBUG=1 npm start
```

### Log Files

The runner doesn't create log files by default. To capture logs:
```bash
npm start > runner.log 2>&1
```

## Security Considerations

- **Token Security**: Never commit `.env` or expose your GitHub PAT
- **Branch Names**: Generated names are sanitized to prevent injection
- **API Scope**: Use minimal required permissions for GitHub PAT
- **Process Lock**: Prevents accidental multiple instances

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following existing patterns
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details