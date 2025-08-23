import { spawn } from 'child_process';
import { CLAUDE_ALLOWED_TOOLS_STRING } from './constants.js';

/**
 * Test just the permission flags to see why Test 2 failed
 */
async function testPermissions() {
  console.log('Testing permission flags...\n');
  console.log('Allowed tools:', CLAUDE_ALLOWED_TOOLS_STRING);
  
  const child = spawn('claude', [
    '--permission-mode', 'acceptEdits', 
    '--allowed-tools', CLAUDE_ALLOWED_TOOLS_STRING,
    '--print',
    'What is 2+2? Just give me the answer.'
  ], {
    stdio: 'inherit'
  });

  child.on('close', (code) => {
    console.log(`\nExited with code: ${code}`);
    if (code !== 0) {
      console.log('Permission flags are causing issues');
    } else {
      console.log('Permission flags work fine!');
    }
  });

  child.on('error', (error) => {
    console.error(`Error: ${error.message}`);
  });
}

testPermissions();