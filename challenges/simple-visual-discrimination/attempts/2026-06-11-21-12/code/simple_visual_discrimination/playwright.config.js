const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 60000,
  use: {
    ...devices["Desktop Chrome"],
    channel: process.env.PLAYWRIGHT_CHANNEL || "chrome",
    headless: process.env.HEADLESS === "0" ? false : true,
    launchOptions: {
      args: ["--no-sandbox", "--window-position=0,0", "--window-size=1280,720"],
    },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
});
