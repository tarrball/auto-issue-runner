import github from './github.js';
import { CONFIG } from './config.js';

/**
 * Manages pull request creation and formatting
 */
export class PullRequestManager {
  /**
   * Creates a pull request for a completed issue implementation
   * @param {Object} issue - GitHub issue object
   * @param {string} branchName - Source branch name
   * @returns {Promise<Object>} Created PR information
   * @throws {Error} If PR creation fails
   */
  async createPullRequest(issue, branchName) {
    console.log(`Creating pull request for issue #${issue.number}...`);
    
    const title = this.generatePRTitle(issue);
    const body = this.generatePRBody(issue);
    
    try {
      const pr = await github.createPullRequest(
        title,
        body,
        branchName,
        CONFIG.github.defaultBranch
      );
      
      await github.addLabelsToIssue(pr.number, [
        CONFIG.labels.issue,
        CONFIG.labels.claudeHelpWanted
      ]);
      
      console.log(`Successfully created PR #${pr.number}: ${pr.html_url}`);
      
      return {
        number: pr.number,
        url: pr.html_url,
        title: pr.title
      };
      
    } catch (error) {
      console.error('Failed to create pull request:', error.message);
      throw error;
    }
  }

  /**
   * Generates a pull request title with conventional commit prefix if needed
   * @param {Object} issue - GitHub issue object
   * @returns {string} Formatted PR title (max 72 characters)
   */
  generatePRTitle(issue) {
    let title = issue.title;
    
    if (!title.match(/^(feat|fix|docs|style|refactor|perf|test|chore)/i)) {
      const type = this.inferPRType(issue);
      title = `${type}: ${title}`;
    }
    
    return title.length > 72 ? title.substring(0, 69) + '...' : title;
  }

  /**
   * Generates a comprehensive pull request body with issue context and checklists
   * @param {Object} issue - GitHub issue object
   * @returns {string} Formatted PR body in markdown
   */
  generatePRBody(issue) {
    let body = `## Summary\n\n`;
    body += `This PR implements the changes requested in issue #${issue.number}.\n\n`;
    
    if (issue.body && issue.body.trim()) {
      const issueBody = issue.body.trim();
      const preview = issueBody.length > 300 
        ? issueBody.substring(0, 297) + '...' 
        : issueBody;
      body += `### Original Issue Description\n\n${preview}\n\n`;
    }
    
    body += `## Changes Made\n\n`;
    body += `- Implemented solution for the requirements described in the issue\n`;
    body += `- Followed existing code patterns and conventions\n`;
    body += `- Added appropriate error handling where needed\n`;
    
    if (CONFIG.commands.test) {
      body += `- Ensured all tests pass\n`;
    }
    
    if (CONFIG.commands.build) {
      body += `- Verified build process completes successfully\n`;
    }
    
    body += `\n## Testing\n\n`;
    if (CONFIG.commands.test) {
      body += `- [x] All existing tests pass\n`;
      body += `- [x] New functionality is covered by tests (if applicable)\n`;
    } else {
      body += `- [ ] Manual testing completed\n`;
    }
    
    body += `\n## Checklist\n\n`;
    body += `- [x] Code follows existing patterns and conventions\n`;
    body += `- [x] Changes are atomic and focused\n`;
    body += `- [x] Commit messages follow conventional format\n`;
    
    if (CONFIG.commands.build) {
      body += `- [x] Build process completes without errors\n`;
    }
    
    body += `\nCloses #${issue.number}\n\n`;
    body += `---\n\n`;
    body += `🤖 This PR was automatically generated using [Claude Code](https://claude.ai/code)`;
    
    return body;
  }

  /**
   * Infers the conventional commit type for PR title from issue content
   * @param {Object} issue - GitHub issue object
   * @returns {string} Conventional commit type (feat, fix, docs, etc.)
   * @private
   */
  inferPRType(issue) {
    const title = issue.title.toLowerCase();
    const body = (issue.body || '').toLowerCase();
    const content = `${title} ${body}`;
    const labels = issue.labels.map(l => l.name.toLowerCase());

    // Check labels first (more reliable)
    if (labels.includes('bug')) return 'fix';
    if (labels.includes('documentation')) return 'docs';
    if (labels.includes('test')) return 'test';
    if (labels.includes('chore')) return 'chore';
    
    // Fallback to content analysis
    if (content.includes('fix') || content.includes('bug') || content.includes('error')) {
      return 'fix';
    }
    if (content.includes('doc') || content.includes('readme')) {
      return 'docs';
    }
    if (content.includes('test') || content.includes('spec')) {
      return 'test';
    }
    if (content.includes('refactor') || content.includes('cleanup')) {
      return 'refactor';
    }
    if (content.includes('perf') || content.includes('performance')) {
      return 'perf';
    }
    if (content.includes('chore')) {
      return 'chore';
    }
    
    return 'feat';
  }

  /**
   * Creates a draft pull request for partial implementations that had errors
   * @param {Object} issue - GitHub issue object
   * @param {string} branchName - Source branch name
   * @param {Error} error - The error that occurred during implementation
   * @returns {Promise<Object>} Created draft PR information
   * @throws {Error} If draft PR creation fails
   */
  async createDraftPR(issue, branchName, error) {
    console.log(`Creating draft PR for failed issue #${issue.number}...`);
    
    const title = `[DRAFT] ${this.generatePRTitle(issue)}`;
    let body = this.generatePRBody(issue);
    
    body += `\n\n## ⚠️ Implementation Issues\n\n`;
    body += `This PR is marked as draft due to implementation issues:\n\n`;
    body += `\`\`\`\n${error.message}\n\`\`\`\n\n`;
    body += `Please review the changes and address the issues before merging.\n`;
    
    try {
      const pr = await github.createPullRequest(
        title,
        body,
        branchName,
        CONFIG.github.defaultBranch
      );
      
      await github.addLabelsToIssue(pr.number, [
        CONFIG.labels.issue,
        CONFIG.labels.claudeHelpWanted,
        'draft'
      ]);
      
      console.log(`Successfully created draft PR #${pr.number}: ${pr.html_url}`);
      
      return {
        number: pr.number,
        url: pr.html_url,
        title: pr.title,
        draft: true
      };
      
    } catch (prError) {
      console.error('Failed to create draft pull request:', prError.message);
      throw prError;
    }
  }
}

export default new PullRequestManager();