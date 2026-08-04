/**
 * Human-paced Playwright participant flow for evidence recording.
 */

const { chromium } = require("@playwright/test");

const AD_URL =
  process.env.AD_URL ||
  "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair";

const TRIALS = [
  ["low", "high"],
  ["low", "medium", "high"],
  ["high", "low", "medium"],
  ["medium", "high", "low", "medium"],
  ["low", "low", "high", "medium"],
];

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function clickNext(page) {
  await page.getByRole("button", { name: "Next" }).first().click();
}

async function reproduceSequence(page, sequence) {
  for (const label of sequence) {
    const title = label.charAt(0).toUpperCase() + label.slice(1);
    const button = page.locator(`button.push-button:has-text("${title}")`).first();
    await button.waitFor({ state: "visible", timeout: 15000 });
    await pause(500);
    await button.click();
  }
  await pause(700);
  await clickNext(page);
  await pause(1200);
}

async function main() {
  const browser = await chromium.launch({
    headless: false,
    args: ["--window-size=1280,720", "--autoplay-policy=no-user-gesture-required"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
  });
  const page = await context.newPage();

  await page.goto(AD_URL, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Begin Experiment" }).click();
  await pause(1500);

  // Consent
  await clickNext(page);
  await pause(1500);

  // Instructions
  await page.waitForSelector("text=Audio memory sequence task", { timeout: 30000 });
  await pause(1500);
  await clickNext(page);
  await pause(1500);

  // Volume calibration
  await page.waitForSelector("text=comfortable level", { timeout: 30000 });
  await pause(2500);
  await clickNext(page);
  await pause(1500);

  for (const sequence of TRIALS) {
    await page.waitForSelector("text=Listen carefully", { timeout: 30000 });
    const listenMs = 1500 + sequence.length * 900;
    await pause(listenMs);
    await clickNext(page);
    await pause(1200);
    await page.waitForSelector("text=Reproduce the sequence", { timeout: 15000 });
    await reproduceSequence(page, sequence);
  }

  await page.waitForSelector("text=completed the audio memory sequence", {
    timeout: 30000,
  });
  await pause(2000);
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
