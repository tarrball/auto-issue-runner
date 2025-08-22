import { CONFIG } from './config.js';
import ProcessLock from './lock.js';
import issueSelector from './issues.js';
import claudeHandler from './claude.js';
import gitOps from './git.js';
import prManager from './pr.js';

/**
 * Main orchestrator class that manages the continuous issue processing workflow
 */
export class AutoIssueRunner {
  constructor() {
    this.lock = new ProcessLock();
    this.isRunning = false;
    this.cycleResults = [];
  }

  /**
   * Starts the auto issue runner with process lock and initial cycle
   * @throws {Error} If startup fails (will exit process)
   */
  async start() {
    try {
      console.log('🚀 Starting Auto Issue Runner...');
      console.log(`Repository: ${CONFIG.github.owner}/${CONFIG.github.repo}`);
      console.log(`Polling interval: ${CONFIG.polling.intervalMs / 1000}s`);
      
      await this.lock.acquire();
      this.lock.setupGracefulShutdown();
      
      this.isRunning = true;
      
      await this.runInitialCycle();
      
      if (this.isRunning) {
        this.startPolling();
      }
      
    } catch (error) {
      console.error('Failed to start runner:', error.message);
      await this.cleanup();
      process.exit(1);
    }
  }

  /**
   * Runs the first cycle immediately after startup
   * @private
   */
  async runInitialCycle() {
    console.log('Running initial cycle...');
    await this.runCycle();
  }

  /**
   * Starts the polling interval to continuously check for new issues
   * @private
   */
  startPolling() {
    console.log(`Starting polling every ${CONFIG.polling.intervalMs / 1000} seconds...`);
    
    this.pollingInterval = setInterval(async () => {
      if (this.isRunning) {
        await this.runCycle();
      }
    }, CONFIG.polling.intervalMs);
  }

  /**
   * Executes one complete cycle: find issue → implement → test → commit → create PR
   * @private
   */
  async runCycle() {
    const cycleStart = Date.now();
    console.log(`\n=== Starting new cycle at ${new Date().toISOString()} ===`);
    
    const result = {
      timestamp: new Date().toISOString(),
      issue: null,
      branch: null,
      pr_number: null,
      status: 'unknown',
      error: null,
      duration_ms: 0
    };

    try {
      const issue = await issueSelector.findEligibleIssue();
      
      if (!issue) {
        result.status = 'NO_ISSUES';
        console.log('✅ No eligible issues found');
        this.logCycleResult(result);
        return;
      }

      result.issue = issue.number;
      
      const branchName = issueSelector.generateBranchName(issue);
      result.branch = branchName;
      
      console.log(`Processing issue #${issue.number}: ${issue.title}`);
      console.log(`Branch: ${branchName}`);
      
      await gitOps.syncWithDefault();
      await gitOps.createAndCheckoutBranch(branchName);
      
      const issueContext = issueSelector.generateIssueContext(issue);
      const repoContext = await claudeHandler.generateRepoContext();
      issue.context = issueContext;
      
      const promptPath = await claudeHandler.createPromptFile(issue, repoContext);
      
      try {
        await claudeHandler.invokeClaude(promptPath, 1);
        
        const testsPass = await gitOps.runTests();
        const buildPass = await gitOps.runBuild();
        
        if (!testsPass || !buildPass) {
          throw new Error('Tests or build failed after Claude implementation');
        }
        
        if (await gitOps.hasChanges()) {
          const commitMessage = gitOps.generateCommitMessage(issue);
          await gitOps.addAllChanges();
          await gitOps.createCommit(commitMessage);
          await gitOps.pushBranch(branchName);
          
          const pr = await prManager.createPullRequest(issue, branchName);
          result.pr_number = pr.number;
          result.status = 'SUCCESS';
          
          console.log(`✅ Successfully processed issue #${issue.number}`);
          console.log(`📝 PR created: ${pr.url}`);
        } else {
          result.status = 'NO_CHANGES';
          console.log(`⚠️  No changes made for issue #${issue.number}`);
        }
        
      } catch (claudeError) {
        console.error(`❌ Claude/build error for issue #${issue.number}:`, claudeError.message);
        
        if (await gitOps.hasChanges()) {
          const commitMessage = `WIP: Attempted fix for issue #${issue.number}\n\nPartial implementation due to: ${claudeError.message}\n\n🤖 Generated with Claude Code`;
          await gitOps.addAllChanges();
          await gitOps.createCommit(commitMessage);
          await gitOps.pushBranch(branchName);
          
          const pr = await prManager.createDraftPR(issue, branchName, claudeError);
          result.pr_number = pr.number;
          result.status = 'PARTIAL';
          result.error = claudeError.message;
          
          console.log(`⚠️  Created draft PR for partial work: ${pr.url}`);
        } else {
          result.status = 'FAILED';
          result.error = claudeError.message;
        }
      }
      
    } catch (error) {
      console.error('❌ Cycle failed:', error.message);
      result.status = 'ERROR';
      result.error = error.message;
    } finally {
      await claudeHandler.cleanup();
      result.duration_ms = Date.now() - cycleStart;
      this.logCycleResult(result);
    }
  }

  /**
   * Logs the result of a cycle and stores it for statistics
   * @param {Object} result - Cycle result object
   * @private
   */
  logCycleResult(result) {
    this.cycleResults.push(result);
    
    const summary = {
      timestamp: result.timestamp,
      issue: result.issue,
      branch: result.branch,
      pr_number: result.pr_number,
      status: result.status,
      duration_ms: result.duration_ms
    };
    
    if (result.error) {
      summary.error = result.error;
    }
    
    console.log('📊 Cycle Result:', JSON.stringify(summary, null, 2));
    
    if (result.status === 'NO_ISSUES') {
      console.log('🎯 All eligible issues processed. Runner will continue polling...');
    }
  }

  /**
   * Stops the runner gracefully, clearing intervals and cleaning up resources
   */
  async stop() {
    console.log('🛑 Stopping Auto Issue Runner...');
    this.isRunning = false;
    
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    
    await this.cleanup();
  }

  /**
   * Cleans up resources and releases the process lock
   * @private
   */
  async cleanup() {
    await claudeHandler.cleanup();
    await this.lock.release();
  }

  /**
   * Generates statistics about runner performance and cycle results
   * @returns {Object} Statistics including counts, durations, and success rates
   */
  getStats() {
    const stats = {
      total_cycles: this.cycleResults.length,
      successful: this.cycleResults.filter(r => r.status === 'SUCCESS').length,
      partial: this.cycleResults.filter(r => r.status === 'PARTIAL').length,
      failed: this.cycleResults.filter(r => r.status === 'FAILED').length,
      no_issues: this.cycleResults.filter(r => r.status === 'NO_ISSUES').length,
      errors: this.cycleResults.filter(r => r.status === 'ERROR').length
    };
    
    if (this.cycleResults.length > 0) {
      const durations = this.cycleResults.map(r => r.duration_ms);
      stats.avg_duration_ms = Math.round(durations.reduce((a, b) => a + b, 0) / durations.length);
      stats.total_duration_ms = durations.reduce((a, b) => a + b, 0);
    }
    
    return stats;
  }
}

export default new AutoIssueRunner();