import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
dotenv.config();
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : 8,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
    ['allure-playwright']
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http:
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    timeout: 60000,
    globalTimeout: 600000,
    actionTimeout: 10000,
    navigationTimeout: 30000,
    extraHTTPHeaders: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**accessibility*.spec.ts',
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
      testMatch: '**/accessibility*.spec.ts',
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
      testMatch: '**/mobile*.spec.ts',
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
      testMatch: '**/mobile*.spec.ts',
    },
  ],
  webServer: [
    {
      command: 'cd ../backend && python manage.py runserver 0.0.0.0:8000',
      port: 8000,
      reuseExistingServer: true,
      timeout: 120000,
    },
    {
      command: 'cd ../frontend && npm run dev',
      port: 3003,
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
  expect: {
    timeout: 5000,
    toMatchSnapshot: {
      threshold: 0.2,
    },
  },
});