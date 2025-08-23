import { spawn } from 'child_process';
import { CLAUDE_ALLOWED_TOOLS_STRING } from './constants.js';

/**
 * Test Claude invocation with different approaches
 */
async function testClaude() {
  console.log('Testing Claude CLI integration...\n');

  // Test 1: Very basic test without any flags
  console.log('=== Test 1: Basic test (no flags) ===');
  await testBasicClaude('What is 2+2?');

  // Test 2: With permission flags
  console.log('\n=== Test 2: With permission flags ===');
  await testClaudeCommand('What is 2+2?');

  // Test 3: Using stdin instead of argument (might fix the issue)
  console.log('\n=== Test 3: Using stdin ===');
  await testClaudeWithStdin('List the files in the current directory using ls.');
}

function testBasicClaude(prompt) {
  return new Promise((resolve, reject) => {
    console.log(`Prompt: ${prompt}`);
    console.log('Executing claude --print (basic)...\n');

    const child = spawn('claude', ['--print', prompt], {
      stdio: 'inherit'  // This forwards all stdio directly to parent process
    });

    child.on('close', (code) => {
      console.log(`\nExited with code: ${code}`);
      resolve({ exitCode: code });
    });

    child.on('error', (error) => {
      console.error(`Spawn error: ${error.message}`);
      reject(error);
    });

    // Timeout after 30 seconds
    setTimeout(() => {
      console.log('Killing process due to timeout...');
      child.kill('SIGTERM');
      reject(new Error('Test timed out'));
    }, 30000);
  });
}

function testClaudeCommand(prompt) {
  return new Promise((resolve, reject) => {
    console.log(`Prompt: ${prompt}`);
    console.log('Executing claude --print with flags...\n');

    const child = spawn('claude', [
      '--permission-mode', 'acceptEdits',
      '--allowed-tools', CLAUDE_ALLOWED_TOOLS_STRING,
      '--print',
      prompt,
    ], {
      stdio: 'inherit'
    });

    child.on('close', (code) => {
      console.log(`\nExited with code: ${code}`);
      resolve({ exitCode: code });
    });

    child.on('error', (error) => {
      console.error(`Spawn error: ${error.message}`);
      reject(error);
    });

    // Timeout after 30 seconds
    setTimeout(() => {
      console.log('Killing process due to timeout...');
      child.kill('SIGTERM');
      reject(new Error('Test timed out'));
    }, 30000);
  });
}

function testClaudeWithStdin(prompt) {
  return new Promise((resolve, reject) => {
    console.log(`Prompt: ${prompt}`);
    console.log('Executing claude --print with stdin...\n');

    const child = spawn('claude', [
      '--print',
      '--permission-mode', 'acceptEdits',
      '--allowed-tools', CLAUDE_ALLOWED_TOOLS_STRING
    ], {
      stdio: ['pipe', 'inherit', 'inherit']  // pipe stdin, inherit stdout/stderr
    });

    child.on('close', (code) => {
      console.log(`\nExited with code: ${code}`);
      resolve({ exitCode: code });
    });

    child.on('error', (error) => {
      console.error(`Spawn error: ${error.message}`);
      reject(error);
    });

    // Send prompt via stdin
    child.stdin.write(prompt);
    child.stdin.end();

    // Timeout after 30 seconds
    setTimeout(() => {
      console.log('Killing process due to timeout...');
      child.kill('SIGTERM');
      reject(new Error('Test timed out'));
    }, 30000);
  });
}

testClaude().catch(error => {
  console.error('Test failed:', error.message);
  process.exit(1);
});