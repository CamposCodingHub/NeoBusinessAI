import { defineConfig } from '@playwright/test';

const headedMode = process.argv.includes('--headed');

export default defineConfig({
  testDir: './e2e',
  timeout: 240000,
  expect: {
    timeout: 20000,
  },
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:3000',
    headless: !headedMode,
    launchOptions: headedMode
      ? {
          slowMo: 450,
        }
      : undefined,
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  reporter: [
    ['list'],
    ['json', { outputFile: '../relatorios_melhorias/logs_erros/playwright-results.json' }],
  ],
});
