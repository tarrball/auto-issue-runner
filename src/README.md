# Auto Issue Runner

⚠️ This was a `node` project that was tested and working. It had some issues, so I converted it to Python. I haven't tested it out much yet.

A Python automation tool that continuously works through GitHub issues by invoking Claude Code to implement solutions and create pull requests.

## ✨ Key Improvements

This Python rewrite addresses the concurrency and process management issues from the Node.js version:

- **🔒 Single PR Limit**: Only one Claude PR open at any time (prevents overlapping work)
- **⚡ Proper Async Coordination**: No more intermingled output or timing issues
- **🛡️ Better Process Management**: Reliable subprocess handling with proper cleanup
- **📊 Comprehensive Logging**: Colorful, structured logging with clear progress tracking
- **🧹 Robust Cleanup**: Automatic cleanup of temporary files before commits
- **🔄 Graceful Shutdown**: Clean stop on Ctrl+C with proper resource cleanup

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Claude Code CLI** installed and accessible in PATH
- **Git** configured with appropriate credentials
- **GitHub Personal Access Token** with required permissions

### Installation

1. **Setup development environment:**
   ```bash
   cd rewrite
   make dev-setup
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install package and dependencies:**
   ```bash
   make install
   # Or manually: pip install -e .[dev]
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run quality checks:**
   ```bash
   make check  # Runs format, lint, typecheck, test
   ```

5. **Run the tool:**
   ```bash
   make run
   # Or: python -m auto_issue_runner.main
   # Or: auto-issue-runner (after install)
   ```

## ⚙️ Configuration

Edit your `.env` file with these required settings:

```bash
# GitHub Configuration
GITHUB_PAT=ghp_your_token_here
GITHUB_OWNER=your-username
GITHUB_REPO=your-repo
GITHUB_REPO_URL=https://github.com/your-username/your-repo.git

# Working Directory (where Claude will operate)
CLAUDE_WORKING_DIRECTORY=/path/to/your/target/repository

# Optional Settings
GITHUB_DEFAULT_BRANCH=main
ISSUE_LABEL=auto
CLAUDE_HELP_WANTED_LABEL=claude-help-wanted
TEST_COMMAND=npm test
BUILD_COMMAND=npm run build
CLAUDE_TIMEOUT_MS=300000
POLLING_INTERVAL_MS=180000
```

## 🎯 How It Works

### Single PR Policy
- ✅ **Processes issues** when no Claude PRs are open
- 🚫 **Waits and polls** when there's an open Claude PR
- 📝 **Shows which PRs** are blocking new work

### Processing Flow
1. **🔍 Issue Discovery**: Finds eligible issues (with required labels, unassigned)
2. **🌿 Branch Creation**: Creates `auto/<issue-number>-<slug>` branches  
3. **🤖 Claude Invocation**: Runs Claude with comprehensive context and permissions
4. **🧪 Testing & Building**: Executes configured test/build commands
5. **💾 Commit & Push**: Creates conventional commits and pushes changes
6. **📝 Pull Request**: Opens PR with detailed description linking to issue

### Async Coordination
- **No overlapping cycles**: Previous cycle must complete before next begins
- **Clean subprocess management**: Proper Claude process handling with timeouts
- **Graceful shutdown**: Ctrl+C waits for current cycle to finish, then cleans up

## 🛠️ Development

### Project Structure
```
auto_issue_runner/
├── __init__.py
├── main.py              # Entry point and CLI
├── config.py            # Configuration management with validation
├── logging_config.py    # Colorful logging setup
├── runner.py            # Main orchestrator with async coordination
├── github_client.py     # GitHub API client with retry logic
├── issue_selector.py    # Issue selection with single PR limit
├── claude_handler.py    # Claude subprocess management
├── git_operations.py    # Git commands with proper working directory
├── pr_manager.py        # Pull request creation
└── process_lock.py      # Process locking and signal handling
```

### Key Features

#### 🔒 Process Locking
Prevents multiple instances from running simultaneously:
```python
# Acquires lock in target repository
await self.process_lock.acquire()
```

#### 🤖 Claude Integration  
Robust subprocess management with proper permissions:
```python
# No more "permission denied" prompts
ALLOWED_TOOLS = [
    "Read(**)", "Edit(**)", 
    "Bash(git:*,npm:*,ng:*,yarn:*)",
    "Task", "WebFetch", "WebSearch"
]
```

#### 📊 Rich Logging
Colorful, structured output with progress tracking:
```
🚀 Starting Auto Issue Runner...
🔍 Searching for eligible issues...
🎯 Processing issue #123: Add dark mode support
🤖 Invoking Claude (attempt 1/2)...
✅ Successfully processed issue #123
📝 PR created: https://github.com/user/repo/pull/456
```

## 🎛️ Commands

- **Start**: `python -m auto_issue_runner.main`
- **Stop**: Press `Ctrl+C` for graceful shutdown
- **Install as package**: `pip install -e .` (then use `auto-issue-runner` command)

## 🔧 Troubleshooting

### Common Issues

1. **"Claude Code command not found"**
   - Ensure `claude` is in your PATH: `which claude`
   - Install Claude Code if needed

2. **"Working directory doesn't exist"**
   - Check `CLAUDE_WORKING_DIRECTORY` path in `.env`
   - Ensure the path exists and is a git repository

3. **"Permission denied" errors**
   - Check GitHub PAT permissions
   - Ensure git is configured with proper credentials

4. **Process won't start**
   - Check if another instance is running: `ps aux | grep auto-issue-runner`
   - Remove stale lock file: `rm /path/to/repo/.auto-runner.lock`

### Target Repository Setup

Add these to your target repository's `.gitignore`:
```gitignore
# Auto-runner temporary files
.auto-runner.lock
issue_prompt.md
debug_claude_prompt.md
```

## 📈 Monitoring

The runner provides detailed statistics:
- **Cycle completion rate**
- **Average processing time**
- **Success/failure breakdown**
- **Real-time progress logs**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
