import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

config({ path: join(__dirname, '..', '.env') });

/**
 * Gets a required environment variable, throwing an error if not set
 * @param {string} key - The environment variable name
 * @returns {string} The environment variable value
 * @throws {Error} When the environment variable is not set
 */
function getRequiredEnv(key) {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Required environment variable ${key} is not set`);
  }
  return value;
}

/**
 * Gets an optional environment variable with a default value
 * @param {string} key - The environment variable name
 * @param {string|undefined} defaultValue - Default value if env var is not set
 * @returns {string|undefined} The environment variable value or default
 */
function getOptionalEnv(key, defaultValue = undefined) {
  return process.env[key] || defaultValue;
}

export const CONFIG = {
  github: {
    pat: getRequiredEnv('GITHUB_PAT'),
    owner: getRequiredEnv('GITHUB_OWNER'),
    repo: getRequiredEnv('GITHUB_REPO'),
    repoUrl: getRequiredEnv('GITHUB_REPO_URL'),
    defaultBranch: getOptionalEnv('GITHUB_DEFAULT_BRANCH', 'main')
  },
  labels: {
    issue: getOptionalEnv('ISSUE_LABEL', 'auto'),
    claudeHelpWanted: getOptionalEnv('CLAUDE_HELP_WANTED_LABEL', 'claude-help-wanted')
  },
  commands: {
    test: getOptionalEnv('TEST_COMMAND'),
    build: getOptionalEnv('BUILD_COMMAND')
  },
  claude: {
    timeoutMs: parseInt(getOptionalEnv('CLAUDE_TIMEOUT_MS', '300000'), 10),
    workingDirectory: getRequiredEnv('CLAUDE_WORKING_DIRECTORY')
  },
  polling: {
    intervalMs: parseInt(getOptionalEnv('POLLING_INTERVAL_MS', '180000'), 10) // 3 minutes
  }
};

/**
 * Validates the loaded configuration and logs success information
 * @throws {Error} When configuration values are invalid
 */
export function validateConfig() {
  if (CONFIG.claude.timeoutMs < 30000) {
    throw new Error('CLAUDE_TIMEOUT_MS must be at least 30000 (30 seconds)');
  }
  
  if (CONFIG.polling.intervalMs < 60000) {
    throw new Error('POLLING_INTERVAL_MS must be at least 60000 (1 minute)');
  }
  
  console.log('Configuration loaded successfully');
  console.log(`Repository: ${CONFIG.github.owner}/${CONFIG.github.repo}`);
  console.log(`Working Directory: ${CONFIG.claude.workingDirectory}`);
  console.log(`Labels: ${CONFIG.labels.issue}, ${CONFIG.labels.claudeHelpWanted}`);
}