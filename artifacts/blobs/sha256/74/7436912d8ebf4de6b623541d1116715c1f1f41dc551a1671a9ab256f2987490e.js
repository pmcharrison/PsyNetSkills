module.exports = {
  testDir: './tests',
  timeout: 180000,
  use: {
    browserName: 'chromium',
    channel: 'chrome',
    headless: false,
    viewport: { width: 1280, height: 720 },
    launchOptions: {
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    },
  },
  reporter: [['line']],
};
