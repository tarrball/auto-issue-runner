import { Octokit } from '@octokit/rest';
import { CONFIG } from './config.js';

/**
 * GitHub API client with rate limiting and retry logic
 */
class GitHubClient {
  constructor() {
    this.octokit = new Octokit({
      auth: CONFIG.github.pat,
      userAgent: 'auto-issue-runner/1.0.0'
    });
    this.lastRequestTime = 0;
    this.minDelayMs = 1000; // 1 second between requests
  }

  /**
   * Enforces rate limiting by ensuring minimum delay between requests
   * @private
   */
  async rateLimit() {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;
    
    if (timeSinceLastRequest < this.minDelayMs) {
      const delay = this.minDelayMs - timeSinceLastRequest;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    this.lastRequestTime = Date.now();
  }

  /**
   * Executes an operation with retry logic and rate limiting
   * @param {Function} operation - Async function to execute
   * @param {number} maxRetries - Maximum number of retry attempts
   * @returns {Promise<any>} Result of the operation
   * @private
   */
  async withRetry(operation, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        await this.rateLimit();
        return await operation();
      } catch (error) {
        if (error.status === 403 || error.status === 429) {
          const retryAfter = error.response?.headers?.['retry-after'];
          const delay = retryAfter ? parseInt(retryAfter) * 1000 : Math.pow(2, attempt) * 1000;
          console.log(`Rate limited, waiting ${delay}ms before retry ${attempt}/${maxRetries}`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        
        if (attempt === maxRetries) throw error;
        
        const delay = Math.pow(2, attempt) * 1000;
        console.log(`Request failed, retrying in ${delay}ms (attempt ${attempt}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  /**
   * Searches for issues that meet all eligibility criteria
   * @returns {Promise<Array>} Array of eligible issues, sorted by creation date (oldest first)
   */
  async searchEligibleIssues() {
    const query = [
      `repo:${CONFIG.github.owner}/${CONFIG.github.repo}`,
      `label:"${CONFIG.labels.issue}"`,
      `label:"${CONFIG.labels.claudeHelpWanted}"`,
      'state:open',
      'type:issue',
      'no:assignee'
    ].join('+');

    return this.withRetry(async () => {
      const response = await this.octokit.rest.search.issuesAndPullRequests({
        q: query,
        sort: 'created',
        order: 'asc',
        per_page: 100
      });
      return response.data.items;
    });
  }

  /**
   * Gets all open pull requests created by this bot
   * Note: Filters by branch prefix 'auto/' to identify bot-created PRs
   * @returns {Promise<Array>} Array of open pull requests from this bot
   */
  async getOpenPullRequests() {
    return this.withRetry(async () => {
      // Get all open PRs first, then filter by head branch pattern
      // This is more reliable than using the head parameter which can be restrictive
      const response = await this.octokit.rest.pulls.list({
        owner: CONFIG.github.owner,
        repo: CONFIG.github.repo,
        state: 'open',
        per_page: 100
      });
      
      // Filter to only include PRs with auto/ branch prefix
      return response.data.filter(pr => pr.head.ref.startsWith('auto/'));
    });
  }

  /**
   * Gets detailed information for a specific issue
   * @param {number} issueNumber - The issue number to retrieve
   * @returns {Promise<Object>} Issue data from GitHub API
   */
  async getIssue(issueNumber) {
    return this.withRetry(async () => {
      const response = await this.octokit.rest.issues.get({
        owner: CONFIG.github.owner,
        repo: CONFIG.github.repo,
        issue_number: issueNumber
      });
      return response.data;
    });
  }

  /**
   * Creates a new pull request
   * @param {string} title - PR title
   * @param {string} body - PR description/body
   * @param {string} head - Source branch name
   * @param {string} base - Target branch (defaults to repository's default branch)
   * @returns {Promise<Object>} Created pull request data
   */
  async createPullRequest(title, body, head, base = CONFIG.github.defaultBranch) {
    return this.withRetry(async () => {
      const response = await this.octokit.rest.pulls.create({
        owner: CONFIG.github.owner,
        repo: CONFIG.github.repo,
        title,
        body,
        head,
        base
      });
      return response.data;
    });
  }

  /**
   * Adds labels to an issue or pull request
   * @param {number} issueNumber - Issue or PR number
   * @param {Array<string>} labels - Array of label names to add
   */
  async addLabelsToIssue(issueNumber, labels) {
    return this.withRetry(async () => {
      await this.octokit.rest.issues.addLabels({
        owner: CONFIG.github.owner,
        repo: CONFIG.github.repo,
        issue_number: issueNumber,
        labels
      });
    });
  }

  /**
   * Gets repository content at a specific path
   * @param {string} path - Path to file or directory (empty string for root)
   * @returns {Promise<Object|null>} File/directory content or null if not found
   */
  async getRepoContent(path = '') {
    return this.withRetry(async () => {
      try {
        const response = await this.octokit.rest.repos.getContent({
          owner: CONFIG.github.owner,
          repo: CONFIG.github.repo,
          path
        });
        return response.data;
      } catch (error) {
        if (error.status === 404) return null;
        throw error;
      }
    });
  }

  /**
   * Gets recent commits from the repository
   * @param {number} count - Number of recent commits to retrieve (default: 10)
   * @returns {Promise<Array>} Array of recent commit objects
   */
  async getRecentCommits(count = 10) {
    return this.withRetry(async () => {
      const response = await this.octokit.rest.repos.listCommits({
        owner: CONFIG.github.owner,
        repo: CONFIG.github.repo,
        per_page: count
      });
      return response.data;
    });
  }
}

export default new GitHubClient();