const fs = require("fs");
const path = require("path");
const { chromium } = require("@playwright/test");

const participantUrl = process.env.PARTICIPANT_URL;
if (!participantUrl) {
  throw new Error("Set PARTICIPANT_URL before running participant-flow.js");
}

const evidenceRoot = process.env.EVIDENCE_ROOT || path.resolve(__dirname, "../../evidence");
const screenshotsDir = path.join(evidenceRoot, "screenshots");
fs.mkdirSync(screenshotsDir, { recursive: true });

async function clickIfVisible(page, selector) {
  const locator = page.locator(selector);
  if ((await locator.count()) > 0 && (await locator.first().isVisible())) {
    await locator.first().click();
    return true;
  }
  return false;
}

async function chooseTrialResponse(page) {
  const preferred = ["#a_little", "#very_much", "#not_at_all"];
  for (const selector of preferred) {
    if (await clickIfVisible(page, selector)) {
      return true;
    }
  }
  const fallback = page.locator("input.response[type='radio']").first();
  if ((await fallback.count()) > 0) {
    await fallback.click();
    return true;
  }
  return false;
}

async function run() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: evidenceRoot,
      size: { width: 1280, height: 720 },
    },
  });
  const page = await context.newPage();
  const eventLog = [];

  try {
    await page.goto(participantUrl, { waitUntil: "networkidle", timeout: 120000 });
    eventLog.push({ step: "open_participant_url", url: page.url() });

    const startSelectors = [
      "button:has-text('Begin')",
      "button:has-text('Start')",
      "button:has-text('Accept')",
      "button.push-button",
    ];
    for (const selector of startSelectors) {
      if (await clickIfVisible(page, selector)) {
        eventLog.push({ step: "clicked_start_selector", selector });
        await page.waitForTimeout(1500);
        break;
      }
    }

    if (await clickIfVisible(page, "#consent")) {
      eventLog.push({ step: "accepted_consent" });
      await page.waitForLoadState("networkidle");
    }

    await page.waitForSelector("#next-button", { timeout: 60000 });
    await page.screenshot({
      path: path.join(screenshotsDir, "01-recording-notice.png"),
      fullPage: true,
    });
    eventLog.push({ step: "captured_notice" });

    await page.click("#next-button");
    await page.waitForSelector("#question", { timeout: 60000 });
    await page.screenshot({
      path: path.join(screenshotsDir, "02-first-streaming-trial.png"),
      fullPage: true,
    });
    eventLog.push({ step: "captured_first_trial" });

    let completed = false;
    let trialScreensCaptured = 1;
    for (let iteration = 0; iteration < 20; iteration += 1) {
      const currentUrl = page.url();
      if (currentUrl.includes("/recruiter-exit")) {
        completed = true;
        break;
      }

      await chooseTrialResponse(page);
      await page.waitForTimeout(800);
      if (await clickIfVisible(page, "#next-button")) {
        await page.waitForTimeout(1200);
      } else if (await clickIfVisible(page, "button.push-button")) {
        await page.waitForTimeout(1200);
      } else {
        eventLog.push({ step: "no-advance-button-found", iteration, url: page.url() });
        break;
      }

      if ((await page.locator("#question").count()) > 0 && trialScreensCaptured < 3) {
        trialScreensCaptured += 1;
        const name = `0${trialScreensCaptured}-streaming-trial-${trialScreensCaptured}.png`;
        await page.screenshot({
          path: path.join(screenshotsDir, name),
          fullPage: true,
        });
      }
    }

    await page.waitForTimeout(1000);
    if (page.url().includes("/recruiter-exit")) {
      completed = true;
    }
    await page.screenshot({
      path: path.join(screenshotsDir, "99-exit-state.png"),
      fullPage: true,
    });
    eventLog.push({ step: "captured_exit", completed, url: page.url() });

    fs.writeFileSync(
      path.join(evidenceRoot, "participant-flow-log.json"),
      JSON.stringify({ completed, eventLog }, null, 2),
    );
  } finally {
    await page.close();
    await context.close();
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
