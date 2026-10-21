const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./playwright",
  timeout: 90_000,
  expect: {
    timeout: 10_000,
  },
  reporter: [["list"]],
  use: {
    ...devices["Desktop Chrome"],
    channel: "chrome",
    viewport: { width: 1280, height: 720 },
    launchOptions: {
      args: ["--no-sandbox", "--disable-dev-shm-usage"],
    },
  },
});
