import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import { join } from 'path';
import { CONFIG } from './config.js';
import github from './github.js';

/**
 * Handles Claude Code invocation and context generation
 */
export class ClaudeHandler {
  /**
   * Generates repository context by fetching README, CONTRIBUTING, and recent commits
   * @returns {Promise<string>} Formatted repository context for Claude
   */
  async generateRepoContext() {
    let context = '';
    
    try {
      const readme = await github.getRepoContent('README.md');
      if (readme && readme.content) {
        const readmeContent = Buffer.from(readme.content, 'base64').toString('utf8');
        context += `## Repository README\n\n${readmeContent}\n\n`;
      }
    } catch (error) {
      console.log('No README.md found or accessible');
    }

    try {
      const contributing = await github.getRepoContent('CONTRIBUTING.md');
      if (contributing && contributing.content) {
        const contributingContent = Buffer.from(contributing.content, 'base64').toString('utf8');
        context += `## Contributing Guidelines\n\n${contributingContent}\n\n`;
      }
    } catch (error) {
      console.log('No CONTRIBUTING.md found or accessible');
    }

    try {
      const recentCommits = await github.getRecentCommits(5);
      if (recentCommits.length > 0) {
        context += `## Recent Commits\n\n`;
        recentCommits.forEach(commit => {
          context += `- ${commit.sha.substring(0, 7)}: ${commit.commit.message.split('\n')[0]}\n`;
        });
        context += '\n';
      }
    } catch (error) {
      console.log('Could not fetch recent commits');
    }

    return context;
  }

  /**
   * Creates a comprehensive prompt file for Claude with issue and repository context
   * @param {Object} issue - GitHub issue with context property
   * @param {string} repoContext - Repository context from generateRepoContext()
   * @returns {Promise<string>} Path to the created prompt file
   */
  async createPromptFile(issue, repoContext) {
    const promptContent = `You are working on a GitHub repository issue. Please implement the requested changes following these guidelines:

${repoContext}

${issue.context}

## Implementation Guidelines

1. **Code Quality**: Follow existing patterns and conventions in the codebase
2. **Commit Standards**: Make atomic commits with conventional commit messages
3. **Testing**: Run tests if configured, fix any failures
4. **Documentation**: Update relevant documentation if needed
5. **Error Handling**: Include appropriate error handling and edge cases

## Commands Available

${CONFIG.commands.test ? `- Test command: ${CONFIG.commands.test}` : '- No test command configured'}
${CONFIG.commands.build ? `- Build command: ${CONFIG.commands.build}` : '- No build command configured'}

## Next Steps

Please implement the changes described in the issue. Once complete:
1. Run any configured test/build commands
2. Make atomic, well-described commits
3. The system will automatically create a pull request

Focus on implementing a complete, working solution that addresses all aspects of the issue.`;

    const promptPath = join(process.cwd(), 'issue_prompt.md');
    await fs.writeFile(promptPath, promptContent, 'utf8');
    return promptPath;
  }

  /**
   * Invokes Claude Code with retry logic
   * @param {string} promptPath - Path to the prompt file
   * @param {number} retries - Number of retry attempts (default: 1)
   * @returns {Promise<Object>} Claude Code execution result
   * @throws {Error} When all attempts fail
   */
  async invokeClaude(promptPath, retries = 1) {
    const maxAttempts = retries + 1;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        console.log(`Invoking Claude Code (attempt ${attempt}/${maxAttempts})...`);
        
        const result = await this.runClaudeCommand(promptPath);
        
        console.log('Claude Code completed successfully');
        return result;
        
      } catch (error) {
        console.error(`Claude Code attempt ${attempt} failed:`, error.message);
        
        if (attempt < maxAttempts) {
          console.log(`Retrying in 10 seconds...`);
          await new Promise(resolve => setTimeout(resolve, 10000));
          continue;
        }
        
        throw new Error(`Claude Code failed after ${maxAttempts} attempts: ${error.message}`);
      }
    }
  }

  /**
   * Executes the Claude Code command with timeout handling
   * @param {string} promptPath - Path to prompt file
   * @returns {Promise<Object>} Execution result with stdout, stderr, and exit code
   * @private
   */
  async runClaudeCommand(promptPath) {
    return new Promise((resolve, reject) => {
      const command = 'claude-code';
      const args = [
        '--prompt', `$(cat "${promptPath}")`,
        '--timeout', CONFIG.claude.timeoutMs.toString()
      ];

      console.log(`Executing: ${command} ${args.join(' ')}`);

      const child = spawn(command, args, {
        stdio: 'pipe',
        shell: true
      });

      let stdout = '';
      let stderr = '';
      let timeoutHandle;

      child.stdout?.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        console.log('Claude:', output.trim());
      });

      child.stderr?.on('data', (data) => {
        const output = data.toString();
        stderr += output;
        console.error('Claude Error:', output.trim());
      });

      child.on('close', (code) => {
        if (timeoutHandle) clearTimeout(timeoutHandle);
        
        if (code === 0) {
          resolve({ stdout, stderr, exitCode: code });
        } else {
          reject(new Error(`Claude Code exited with code ${code}. stderr: ${stderr}`));
        }
      });

      child.on('error', (error) => {
        if (timeoutHandle) clearTimeout(timeoutHandle);
        reject(new Error(`Failed to spawn Claude Code: ${error.message}`));
      });

      // Set timeout with buffer beyond Claude's internal timeout
      timeoutHandle = setTimeout(() => {
        child.kill('SIGTERM');
        reject(new Error('Claude Code timed out'));
      }, CONFIG.claude.timeoutMs + 10000);
    });
  }

  /**
   * Cleans up temporary files created during Claude invocation
   */
  async cleanup() {
    try {
      const promptPath = join(process.cwd(), 'issue_prompt.md');
      await fs.unlink(promptPath);
    } catch (error) {
      // Ignore cleanup errors - file may not exist
    }
  }
}

export default new ClaudeHandler();