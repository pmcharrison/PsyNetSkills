module.exports = {
  testDir: './tests',
  reporter: [['list']],
  use: {
    browserName: 'chromium',
    headless: process.env.HEADLESS !== '0',
    launchOptions: {
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
      slowMo: process.env.VISUAL_EVIDENCE === '1' ? 150 : 0,
    },
  },
};
