import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests/e2e',
  webServer: { command: 'npm run dev -- --host 127.0.0.1', url: 'http://127.0.0.1:4321', reuseExistingServer: true },
  use: { baseURL: 'http://127.0.0.1:4321', trace: 'on-first-retry' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Desktop Chrome'], viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true } },
  ],
});
