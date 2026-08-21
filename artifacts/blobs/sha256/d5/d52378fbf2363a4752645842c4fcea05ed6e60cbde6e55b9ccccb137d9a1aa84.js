const fs = require("fs");
const path = require("path");
const { chromium, expect } = require("@playwright/test");

const experimentDir = path.resolve(__dirname, "..");
const attemptDir = path.resolve(experimentDir, "..", "..");
const evidenceDir = path.join(attemptDir, "evidence");
const screenshotDir = path.join(evidenceDir, "screenshots");
const videoDir = path.join(evidenceDir, "playwright-video");

const participantUrl =
  process.env.PARTICIPANT_URL ||
  "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair";
const dashboardUrl =
  process.env.DASHBOARD_URL ||
  "http://127.0.0.1:5000/dashboard/develop";

fs.mkdirSync(screenshotDir, { recursive: true });
fs.mkdirSync(videoDir, { recursive: true });

async function clickButton(page, selector) {
  const locator = selector
    ? page.locator(selector).first()
    : page
        .locator("button:visible:not([disabled]), input[type=submit]:visible:not([disabled])")
        .first();
  await locator.waitFor({ state: "visible", timeout: 15000 });
  await expect(locator).toBeEnabled({ timeout: 15000 });
  await locator.click();
}

async function screenshotOnce(page, name, taken) {
  if (taken.has(name)) return;
  taken.add(name);
  await page.screenshot({ path: path.join(screenshotDir, `${name}.png`), fullPage: true });
}

async function answerTrial(page, bodyText, trialIndex) {
  if (bodyText.includes("same or different") || bodyText.includes("Same (S)")) {
    await clickButton(page, "button#different, button:has-text('Different')");
  } else if (bodyText.includes("Rate how similar")) {
    await clickButton(page, 'button[id="3"]');
  } else if (bodyText.includes("Choose the number")) {
    await clickButton(page, 'button[id="1"]');
  } else {
    await clickButton(page);
  }
  await page.waitForTimeout(trialIndex < 4 ? 350 : 80);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();
  const taken = new Set();
  let trialIndex = 0;

  await page.goto(participantUrl, { waitUntil: "domcontentloaded" });

  for (let step = 0; step < 120; step++) {
    if (page.url().includes("/recruiter-exit")) break;
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    const bodyText = await page.locator("body").innerText({ timeout: 15000 });

    if (bodyText.includes("Visual Psychophysics Battery")) {
      await screenshotOnce(page, "01_intro", taken);
    }
    if (bodyText.includes("Block 1: same or different")) {
      await screenshotOnce(page, "02_discrimination_instructions", taken);
    }
    if (bodyText.includes("Rate how similar")) {
      await screenshotOnce(page, "03_similarity_trial", taken);
    }
    if (bodyText.includes("Choose the number")) {
      await screenshotOnce(page, "04_identification_probe", taken);
    }

    const hasTrialButtons =
      (await page
        .locator('button#same, button#different, button[id="3"], button[id="1"]')
        .count()) > 0;

    if (hasTrialButtons) {
      trialIndex += 1;
      await answerTrial(page, bodyText, trialIndex);
    } else {
      const enabledButtons = await page
        .locator("button:visible:not([disabled]), input[type=submit]:visible:not([disabled])")
        .count();
      if (enabledButtons === 0) {
        await page.waitForTimeout(800);
        continue;
      }
      await clickButton(page);
      await page.waitForTimeout(120);
    }
  }

  await expect(page).toHaveURL(/recruiter-exit/, { timeout: 30000 });
  await screenshotOnce(page, "05_completion", taken);

  const dashboard = await context.newPage();
  await dashboard.goto(dashboardUrl, { waitUntil: "networkidle" });
  await dashboard.screenshot({
    path: path.join(screenshotDir, "06_monitor_dashboard.png"),
    fullPage: true,
  });
  fs.writeFileSync(path.join(evidenceDir, "monitor.html"), await dashboard.content());

  const video = await page.video().path();
  await context.close();
  await browser.close();
  fs.writeFileSync(path.join(evidenceDir, "participant_video_source.txt"), `${video}\n`);
  console.log(`Completed participant flow with ${trialIndex} trial responses.`);
  console.log(`Video source: ${video}`);
})();
