import github from './github.js';
import { CONFIG } from './config.js';

/**
 * Handles issue selection and filtering logic
 */
export class IssueSelector {
  constructor() {
    this.processedIssues = new Set();
  }

  /**
   * Finds the next eligible issue to process
   * Filters out issues that already have open PRs or were processed in this session
   * @returns {Promise<Object|null>} The selected issue object or null if none available
   */
  async findEligibleIssue() {
    try {
      console.log('Searching for eligible issues...');
      
      const issues = await github.searchEligibleIssues();
      
      if (issues.length === 0) {
        console.log('No eligible issues found');
        return null;
      }

      console.log(`Found ${issues.length} eligible issues`);

      const openPRs = await github.getOpenPullRequests();
      const prIssueNumbers = new Set();
      
      // Extract issue numbers from existing PR branch names
      openPRs.forEach(pr => {
        const match = pr.head.ref.match(/^auto\/(\d+)-/);
        if (match) {
          prIssueNumbers.add(parseInt(match[1], 10));
        }
      });

      const availableIssues = issues.filter(issue => {
        if (prIssueNumbers.has(issue.number)) {
          console.log(`Skipping issue #${issue.number}: Open PR exists`);
          return false;
        }
        
        if (this.processedIssues.has(issue.number)) {
          console.log(`Skipping issue #${issue.number}: Already processed in this session`);
          return false;
        }
        
        return true;
      });

      if (availableIssues.length === 0) {
        console.log('No available issues (all have open PRs or were processed)');
        return null;
      }

      const selectedIssue = availableIssues[0];
      console.log(`Selected issue #${selectedIssue.number}: ${selectedIssue.title}`);
      
      this.processedIssues.add(selectedIssue.number);
      
      return await github.getIssue(selectedIssue.number);
      
    } catch (error) {
      console.error('Error finding eligible issue:', error.message);
      throw error;
    }
  }

  /**
   * Generates a git branch name from an issue
   * Format: auto/<issue-number>-<sanitized-title-slug>
   * @param {Object} issue - GitHub issue object
   * @returns {string} Git branch name
   */
  generateBranchName(issue) {
    const slug = issue.title
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
      .replace(/\s+/g, '-')         // Replace spaces with hyphens
      .substring(0, 40)             // Limit length
      .replace(/-+$/, '');          // Remove trailing hyphens
    
    return `auto/${issue.number}-${slug}`;
  }

  /**
   * Generates comprehensive context information for Claude from a GitHub issue
   * @param {Object} issue - GitHub issue object
   * @returns {string} Formatted markdown context for Claude
   */
  generateIssueContext(issue) {
    let context = `# Issue #${issue.number}: ${issue.title}\n\n`;
    context += `**Created by:** ${issue.user.login}\n`;
    context += `**Created at:** ${issue.created_at}\n`;
    context += `**Labels:** ${issue.labels.map(l => l.name).join(', ')}\n\n`;
    
    if (issue.body && issue.body.trim()) {
      context += `## Description\n\n${issue.body}\n\n`;
    }
    
    context += `## Acceptance Criteria\n\n`;
    context += 'Please implement the feature/fix described above. ';
    context += 'Follow the existing code patterns and conventions in the repository. ';
    context += 'Write clear, atomic commits with conventional commit messages. ';
    context += 'Ensure tests pass if a test command is configured.\n\n';
    
    context += `**Issue URL:** ${issue.html_url}\n`;
    
    return context;
  }
}

export default new IssueSelector();