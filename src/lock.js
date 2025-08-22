import { promises as fs } from 'fs';
import { join } from 'path';

const LOCK_FILE = '.auto-runner.lock';
const LOCK_PATH = join(process.cwd(), LOCK_FILE);

class ProcessLock {
  constructor() {
    this.lockAcquired = false;
    this.pid = process.pid;
  }

  async isProcessRunning(pid) {
    try {
      process.kill(pid, 0);
      return true;
    } catch (error) {
      return false;
    }
  }

  async acquire() {
    try {
      const lockData = await fs.readFile(LOCK_PATH, 'utf8');
      const existingPid = parseInt(lockData.trim(), 10);
      
      if (await this.isProcessRunning(existingPid)) {
        throw new Error(`Auto runner already running with PID ${existingPid}`);
      }
      
      console.log(`Cleaning up stale lock file from PID ${existingPid}`);
      await fs.unlink(LOCK_PATH);
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }
    }

    await fs.writeFile(LOCK_PATH, this.pid.toString(), 'utf8');
    this.lockAcquired = true;
    console.log(`Lock acquired with PID ${this.pid}`);
  }

  async release() {
    if (!this.lockAcquired) return;
    
    try {
      await fs.unlink(LOCK_PATH);
      this.lockAcquired = false;
      console.log(`Lock released for PID ${this.pid}`);
    } catch (error) {
      if (error.code !== 'ENOENT') {
        console.error('Failed to release lock:', error.message);
      }
    }
  }

  /**
   * Sets up graceful shutdown handlers to ensure lock is released on exit
   * Handles SIGINT, SIGTERM, uncaught exceptions, and unhandled rejections
   */
  setupGracefulShutdown() {
    const cleanup = async () => {
      console.log('\\nReceived shutdown signal, cleaning up...');
      await this.release();
      process.exit(0);
    };

    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);
    process.on('uncaughtException', async (error) => {
      console.error('Uncaught exception:', error);
      await this.release();
      process.exit(1);
    });
    process.on('unhandledRejection', async (reason) => {
      console.error('Unhandled rejection:', reason);
      await this.release();
      process.exit(1);
    });
  }
}

export default ProcessLock;