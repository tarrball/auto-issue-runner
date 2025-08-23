# Auto Issue Runner

A Python automation tool that continuously works through GitHub issues by invoking Claude Code to implement solutions and create pull requests.

## ✨ Key Features

- 🔒 **Single PR Policy**: Only one Claude PR open at any time (prevents conflicts)
- ⚡ **Proper Async Coordination**: No more intermingled output or timing issues  
- 🛡️ **Better Process Management**: Reliable subprocess handling with proper cleanup
- 🤖 **Claude Integration**: Pre-approved tool permissions for autonomous operation
- 📊 **Comprehensive Logging**: Colorful, structured logging with progress tracking
- 🧹 **Robust Cleanup**: Automatic cleanup of temporary files before commits
- 🔄 **Graceful Shutdown**: Clean stop on Ctrl+C with proper resource cleanup

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Claude Code CLI** installed and accessible in PATH
- **Git** configured with appropriate credentials  
- **GitHub Personal Access Token** with required permissions

### Installation

1. **Setup development environment:**
   ```bash
   cd src
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
# GitHub Configuration (Required)
GITHUB_PAT=ghp_your_personal_access_token_here
GITHUB_OWNER=your-github-username
GITHUB_REPO=your-repository-name
GITHUB_REPO_URL=https://github.com/your-username/your-repo.git

# Working Directory (Required) - where Claude will operate
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

### GitHub PAT Permissions

Your Personal Access Token should have the following permissions for the target repository:

- **Contents**: Read and Write
- **Pull requests**: Read and Write  
- **Issues**: Read and Write
- **Metadata**: Read

## 🎯 How It Works

### Single PR Policy
- ✅ **Processes issues** when no Claude PRs are open
- 🚫 **Waits and polls** when there's an open Claude PR
- 📝 **Shows which PRs** are blocking new work

### Issue Selection Rules

The runner will process issues that meet ALL of the following criteria:

- ✅ **Open state**
- ✅ **Has both required labels** (`ISSUE_LABEL` AND `CLAUDE_HELP_WANTED_LABEL`)
- ✅ **Unassigned**
- ✅ **No open Claude PRs exist** (single PR policy)
- ✅ **Oldest first** (FIFO processing)

### Processing Flow

1. **🔍 Issue Discovery**: Finds eligible issues (with required labels, unassigned)
2. **🚫 Single PR Check**: Only proceeds when no Claude PRs are open
3. **🌿 Branch Creation**: Creates `auto/<issue-number>-<slug>` branches with sanitization
4. **🤖 Claude Invocation**: Runs Claude with comprehensive context and pre-approved permissions
5. **🧪 Testing & Building**: Executes configured test/build commands with proper working directory
6. **💾 Commit & Push**: Creates conventional commits and pushes changes
7. **📝 Pull Request**: Opens PR with detailed description linking to issue

### Async Coordination
- **No overlapping cycles**: Previous cycle must complete before next begins
- **Clean subprocess management**: Proper Claude process handling with timeouts
- **Graceful shutdown**: Ctrl+C waits for current cycle to finish, then cleans up

## 🛠️ Development

### Project Structure
```
src/auto_issue_runner/
├── __init__.py
├── main.py              # Entry point and CLI
├── config.py            # Pydantic configuration with validation
├── logging_config.py    # Colorful logging setup
├── runner.py            # Main orchestrator with async coordination
├── github_client.py     # GitHub API client with retry logic
├── issue_selector.py    # Issue selection with single PR limit
├── claude_handler.py    # Claude subprocess management
├── git_operations.py    # Git commands with proper working directory
├── pr_manager.py        # Pull request creation
├── process_lock.py      # Process locking and signal handling
└── validators.py        # Input validation for security
```

### Quality Tools

Run individual tools or all together:

```bash
make format      # Black code formatting
make lint        # Ruff linting with auto-fix
make typecheck   # MyPy type checking  
make test        # Pytest with coverage
make check       # All of the above
```

### Usage Commands

- **Start**: `make run` or `python -m auto_issue_runner.main`
- **Stop**: Press `Ctrl+C` for graceful shutdown
- **Install as package**: `make install` (enables `auto-issue-runner` command)

## 📊 Monitoring & Output

### Rich Console Logging
```
🚀 Starting Auto Issue Runner...
   Repository: username/repo-name
   Working Directory: /path/to/repo
   Polling Interval: 180s
🔍 Searching for eligible issues...
🚫 Skipping all issues - Claude has open PR(s):
   - PR #123: Fix login bug (auto/456-fix-login-bug)
⏳ Waiting 180s before next cycle...
```

### Statistics
The runner provides detailed statistics:
- **Cycle completion rate**
- **Average processing time**  
- **Success/failure breakdown**
- **Real-time progress logs**

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

## 🔒 Security Features

- **Input validation**: Sanitizes GitHub data to prevent injection attacks
- **Subprocess security**: Uses secure subprocess management (no shell injection)
- **Environment isolation**: Uses `.env` files with templates
- **Token security**: Never logs or exposes secrets
- **Branch name sanitization**: Prevents malicious branch names

## 🚀 Production Ready

This Python version includes enterprise-grade features:

- **🔧 Modern tooling**: Black, Ruff, MyPy with strict configuration
- **🧪 Testing**: Pytest with async support and coverage reporting  
- **📝 Type safety**: Full type annotations with `py.typed` marker
- **📚 Documentation**: Comprehensive docstrings and API documentation
- **🛡️ Security**: Input validation and secure subprocess management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run `make check` to ensure quality
4. Add tests for new functionality  
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details