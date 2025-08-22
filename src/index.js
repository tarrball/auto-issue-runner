#!/usr/bin/env node

import { validateConfig } from './config.js';
import runner from './runner.js';

async function main() {
  try {
    console.log('🔧 Validating configuration...');
    validateConfig();
    
    console.log('✅ Configuration valid');
    
    await runner.start();
    
  } catch (error) {
    console.error('❌ Startup failed:', error.message);
    
    if (error.message.includes('Required environment variable')) {
      console.log('\\n💡 Make sure to:');
      console.log('   1. Copy .env.example to .env');
      console.log('   2. Fill in all required environment variables');
      console.log('   3. Ensure your GitHub PAT has the correct permissions');
    }
    
    process.exit(1);
  }
}

process.on('SIGINT', async () => {
  console.log('\\n🛑 Received SIGINT, shutting down gracefully...');
  await runner.stop();
  
  const stats = runner.getStats();
  console.log('\\n📈 Final Statistics:');
  console.log(JSON.stringify(stats, null, 2));
  
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\\n🛑 Received SIGTERM, shutting down gracefully...');
  await runner.stop();
  process.exit(0);
});

main().catch(async (error) => {
  console.error('💥 Unhandled error:', error);
  await runner.stop();
  process.exit(1);
});