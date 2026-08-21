const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  timeout: 120000,
  use: {
    viewport: { width: 1280, height: 720 },
    video: "off",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
