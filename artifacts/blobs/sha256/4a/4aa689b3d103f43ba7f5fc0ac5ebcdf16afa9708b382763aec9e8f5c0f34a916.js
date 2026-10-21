import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  reporter: [['list']],
  use: {
    ...devices['Desktop Chrome'],
    channel: 'chrome',
    launchOptions: {
      args: ['--window-position=0,0', '--window-size=1280,720'],
    },
    viewport: { width: 1280, height: 720 },
    trace: 'off',
    video: 'off',
  },
});
