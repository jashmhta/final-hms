const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
console.log('🚀 Setting up HMS Enterprise-Grade End-to-End Test Environment...');
const directories = [
    'screenshots',
    'test-results',
    'reports',
    'allure-results',
    'test-data',
    'logs'
];
directories.forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`✅ Created directory: ${dir}`);
    }
});
const envPath = '.env';
if (!fs.existsSync(envPath)) {
    fs.copyFileSync('.env.example', envPath);
    console.log('✅ Created .env file from .env.example');
}
console.log('📦 Installing dependencies...');
try {
    execSync('npm install', { stdio: 'inherit' });
    console.log('✅ Dependencies installed successfully');
} catch (error) {
    console.error('❌ Failed to install dependencies:', error);
    process.exit(1);
}
console.log('🌐 Installing Playwright browsers...');
try {
    execSync('npx playwright install', { stdio: 'inherit' });
    console.log('✅ Playwright browsers installed successfully');
} catch (error) {
    console.error('❌ Failed to install Playwright browsers:', error);
    process.exit(1);
}
console.log('🔍 Verifying system requirements...');
const nodeVersion = process.version;
const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
if (majorVersion < 18) {
    console.error('❌ Node.js version 18 or higher is required. Current version:', nodeVersion);
    process.exit(1);
}
console.log(`✅ Node.js version: ${nodeVersion}`);
try {
    execSync('docker --version', { stdio: 'pipe' });
    console.log('✅ Docker is available');
} catch (error) {
    console.log('⚠️ Docker is not available - some tests may require manual setup');
}
const testDataStructure = [
    'test-data/patients',
    'test-data/appointments',
    'test-data/prescriptions',
    'test-data/billing',
    'test-data/lab-results'
];
testDataStructure.forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`✅ Created test data directory: ${dir}`);
    }
});
console.log('📊 Generating initial test data...');
const generateTestData = require('../utils/generate-test-data');
generateTestData();
console.log('🎉 Test environment setup completed successfully!');
console.log('');
console.log('Next steps:');
console.log('1. Configure your .env file with actual system URLs and credentials');
console.log('2. Ensure the HMS system is running (backend and frontend)');
console.log('3. Run tests with: npm run test:e2e');
console.log('4. For UI mode: npm run test:e2e:ui');