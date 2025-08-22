import { spawn } from 'child_process';
import { CONFIG } from './config.js';

/**
 * Handles all git operations for the auto issue runner
 */
export class GitOperations {
  /**
   * Executes a git command with the given arguments
   * @param {Array<string>} args - Git command arguments
   * @param {Object} options - Additional spawn options
   * @returns {Promise<Object>} Command result with stdout, stderr, and exit code
   * @private
   */
  async runGitCommand(args, options = {}) {
    return new Promise((resolve, reject) => {
      const child = spawn('git', args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: process.cwd(),
        ...options
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve({ stdout: stdout.trim(), stderr: stderr.trim(), exitCode: code });
        } else {
          reject(new Error(`Git command failed (exit ${code}): ${stderr || stdout}`));
        }
      });

      child.on('error', (error) => {
        reject(new Error(`Failed to execute git: ${error.message}`));
      });
    });
  }

  /**
   * Syncs the local repository with the default branch
   * @throws {Error} If git operations fail
   */
  async syncWithDefault() {
    console.log(`Syncing with ${CONFIG.github.defaultBranch} branch...`);
    
    try {
      await this.runGitCommand(['fetch', 'origin']);
      await this.runGitCommand(['checkout', CONFIG.github.defaultBranch]);
      await this.runGitCommand(['pull', 'origin', CONFIG.github.defaultBranch]);
      console.log('Successfully synced with default branch');
    } catch (error) {
      console.error('Failed to sync with default branch:', error.message);
      throw error;
    }
  }

  /**
   * Creates and checks out a new branch, or checks out if it already exists
   * @param {string} branchName - Name of the branch to create/checkout
   * @throws {Error} If git operations fail
   */
  async createAndCheckoutBranch(branchName) {
    console.log(`Creating and checking out branch: ${branchName}`);
    
    try {
      await this.runGitCommand(['checkout', '-b', branchName]);
      console.log(`Successfully created branch: ${branchName}`);
    } catch (error) {
      if (error.message.includes('already exists')) {
        console.log(`Branch ${branchName} already exists, checking out...`);
        await this.runGitCommand(['checkout', branchName]);
      } else {
        throw error;
      }
    }
  }

  /**
   * Checks if there are any uncommitted changes in the repository
   * @returns {Promise<boolean>} True if there are changes, false otherwise
   */
  async hasChanges() {
    try {
      const result = await this.runGitCommand(['status', '--porcelain']);
      return result.stdout.length > 0;
    } catch (error) {
      console.error('Failed to check git status:', error.message);
      return false;
    }
  }

  /**
   * Adds all changes to the git staging area
   * @throws {Error} If git add operation fails
   */
  async addAllChanges() {
    console.log('Adding all changes to staging...');
    try {
      await this.runGitCommand(['add', '.']);
      console.log('Successfully added all changes');
    } catch (error) {
      console.error('Failed to add changes:', error.message);
      throw error;
    }
  }

  /**
   * Creates a git commit with the given message
   * @param {string} message - Commit message (can be multi-line)
   * @throws {Error} If git commit operation fails
   */
  async createCommit(message) {
    console.log('Creating commit...');
    try {
      await this.runGitCommand(['commit', '-m', message]);
      console.log(`Successfully created commit: ${message.split('\n')[0]}`);
    } catch (error) {
      console.error('Failed to create commit:', error.message);
      throw error;
    }
  }

  /**
   * Pushes a branch to the remote origin repository
   * @param {string} branchName - Name of the branch to push
   * @throws {Error} If git push operation fails
   */
  async pushBranch(branchName) {
    console.log(`Pushing branch ${branchName} to origin...`);
    try {
      await this.runGitCommand(['push', '-u', 'origin', branchName]);
      console.log('Successfully pushed branch to origin');
    } catch (error) {
      console.error('Failed to push branch:', error.message);
      throw error;
    }
  }

  /**
   * Runs the configured test command if available
   * @returns {Promise<boolean>} True if tests pass or no test command configured, false if tests fail
   */
  async runTests() {
    if (!CONFIG.commands.test) {
      console.log('No test command configured, skipping tests');
      return true;
    }

    console.log(`Running tests: ${CONFIG.commands.test}`);
    try {
      await this.runCommand(CONFIG.commands.test);
      console.log('Tests passed successfully');
      return true;
    } catch (error) {
      console.error('Tests failed:', error.message);
      return false;
    }
  }

  /**
   * Runs the configured build command if available
   * @returns {Promise<boolean>} True if build succeeds or no build command configured, false if build fails
   */
  async runBuild() {
    if (!CONFIG.commands.build) {
      console.log('No build command configured, skipping build');
      return true;
    }

    console.log(`Running build: ${CONFIG.commands.build}`);
    try {
      await this.runCommand(CONFIG.commands.build);
      console.log('Build completed successfully');
      return true;
    } catch (error) {
      console.error('Build failed:', error.message);
      return false;
    }
  }

  /**
   * Executes a shell command (used for test and build commands)
   * @param {string} command - Command string to execute
   * @returns {Promise<Object>} Command result with exit code
   * @private
   */
  async runCommand(command) {
    return new Promise((resolve, reject) => {
      // Use shell to properly handle complex commands with pipes, quotes, etc.
      const child = spawn(command, [], {
        stdio: 'inherit',
        cwd: process.cwd(),
        shell: true
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve({ exitCode: code });
        } else {
          reject(new Error(`Command failed with exit code ${code}: ${command}`));
        }
      });

      child.on('error', (error) => {
        reject(new Error(`Failed to execute command: ${error.message}`));
      });
    });
  }

  /**
   * Generates a conventional commit message from a GitHub issue
   * @param {Object} issue - GitHub issue object
   * @returns {string} Formatted commit message
   */
  generateCommitMessage(issue) {
    const title = issue.title.length > 50 
      ? issue.title.substring(0, 47) + '...' 
      : issue.title;

    const type = this.inferCommitType(issue);
    const scope = this.inferCommitScope(issue);
    
    let message = `${type}`;
    if (scope) {
      message += `(${scope})`;
    }
    message += `: ${title}`;
    
    message += `\n\nCloses #${issue.number}`;
    
    if (issue.body && issue.body.trim()) {
      const bodyPreview = issue.body.trim().split('\n')[0];
      if (bodyPreview.length > 0 && bodyPreview !== title) {
        message += `\n\n${bodyPreview}`;
      }
    }

    message += `\n\n🤖 Generated with Claude Code`;
    
    return message;
  }

  /**
   * Infers the conventional commit type from issue content
   * @param {Object} issue - GitHub issue object
   * @returns {string} Conventional commit type (feat, fix, docs, etc.)
   * @private
   */
  inferCommitType(issue) {
    const title = issue.title.toLowerCase();
    const body = (issue.body || '').toLowerCase();
    const content = `${title} ${body}`;

    if (content.includes('fix') || content.includes('bug') || content.includes('error')) {
      return 'fix';
    }
    if (content.includes('test') || content.includes('spec')) {
      return 'test';
    }
    if (content.includes('doc') || content.includes('readme')) {
      return 'docs';
    }
    if (content.includes('refactor') || content.includes('cleanup')) {
      return 'refactor';
    }
    if (content.includes('perf') || content.includes('performance')) {
      return 'perf';
    }
    
    return 'feat';
  }

  /**
   * Infers the conventional commit scope from issue labels and title
   * @param {Object} issue - GitHub issue object
   * @returns {string|null} Conventional commit scope or null if none found
   * @private
   */
  inferCommitScope(issue) {
    const labels = issue.labels.map(l => l.name.toLowerCase());
    const title = issue.title.toLowerCase();
    
    const scopeMap = {
      'ui': 'ui',
      'api': 'api',
      'auth': 'auth',
      'database': 'db',
      'db': 'db',
      'config': 'config',
      'deps': 'deps',
      'dependencies': 'deps'
    };

    // Check labels first (more reliable)
    for (const label of labels) {
      if (scopeMap[label]) {
        return scopeMap[label];
      }
    }

    // Fallback to checking title content
    for (const [keyword, scope] of Object.entries(scopeMap)) {
      if (title.includes(keyword)) {
        return scope;
      }
    }

    return null;
  }
}

export default new GitOperations();