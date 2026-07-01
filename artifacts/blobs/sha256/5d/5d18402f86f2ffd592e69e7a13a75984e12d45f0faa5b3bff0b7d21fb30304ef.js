// Playwright configuration for the participant-flow evidence runner.
const { defineConfig } = require("@playwright/test");

const PARTICIPANT_URL =
  process.env.PARTICIPANT_URL ||
  "http://127.0.0.1:5000/ad?recruiter=hotair&generate_tokens=true";

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 180000,
  expect: { timeout: 20000 },
  use: {
    baseURL: PARTICIPANT_URL,
    channel: "chrome",
    headless: true,
    viewport: { width: 1280, height: 720 },
    video: {
      mode: "on",
      size: { width: 1280, height: 720 },
    },
    actionTimeout: 20000,
  },
  reporter: [["list"]],
  outputDir: "./test-results",
});
