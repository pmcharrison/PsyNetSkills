const { chromium } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const participantUrl = process.argv[2];
if (!participantUrl) {
  throw new Error("Usage: node tests/participant-flow.spec.js <participant-url>");
}
const slowFlow = process.env.SLOW_FLOW === "1";
const stepDelayMs = slowFlow ? 900 : 300;
const completionDelayMs = slowFlow ? 2500 : 0;

const evidenceDir = path.resolve(__dirname, "../../../evidence");
const screenshotDir = path.join(evidenceDir, "screenshots");
fs.mkdirSync(screenshotDir, { recursive: true });

const screenshotManifest = {
  captions: {
    "screenshots/01-instructions.png": "Instruction page explaining the 10 adaptive digit-recall trials.",
    "screenshots/02-study-trial.png": "Representative study page showing the digit string to memorize.",
    "screenshots/03-recall-trial.png": "Representative recall page with copy/paste blocked text input.",
    "screenshots/04-completion.png": "Completion state after the participant finishes the task.",
  },
};

async function clickContinue(page) {
  const buttons = page.locator("button:visible, input[type=submit]:visible");
  const count = await buttons.count();
  if (count === 0) {
    throw new Error("No visible button to continue");
  }
  await buttons.nth(count - 1).click();
}

async function visibleText(page) {
  return await page.locator("body").innerText({ timeout: 5000 });
}

(async () => {
  const browser = await chromium.launch({
    channel: "chrome",
    headless: false,
    args: ["--no-sandbox", "--window-size=1280,720"],
  });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  const trialLog = [];
  let lastTarget = null;
  let instructionShot = false;
  let studyShot = false;
  let recallShot = false;

  await page.goto(participantUrl, { waitUntil: "domcontentloaded" });

  for (let step = 0; step < 80; step++) {
    await page.waitForTimeout(stepDelayMs);
    const url = page.url();
    const text = await visibleText(page);

    if (!instructionShot && text.includes("Digit memory task")) {
      await page.screenshot({ path: path.join(screenshotDir, "01-instructions.png") });
      instructionShot = true;
    }

    const targetMatch = text.match(/Remember this digit string:\s*([0-9]+)/);
    if (targetMatch) {
      lastTarget = targetMatch[1];
      trialLog.push({ target: lastTarget, length: lastTarget.length });
      if (!studyShot) {
        await page.screenshot({ path: path.join(screenshotDir, "02-study-trial.png") });
        studyShot = true;
      }
      if (slowFlow) {
        await page.waitForTimeout(1600);
      }
    }

    const input = page.locator("input[type=text]:visible, textarea:visible").first();
    if ((await input.count()) > 0) {
      if (!lastTarget) {
        throw new Error("Recall input appeared before a target was observed");
      }
      if (!recallShot) {
        await page.screenshot({ path: path.join(screenshotDir, "03-recall-trial.png") });
        recallShot = true;
      }
      await input.fill(lastTarget);
      const value = await input.inputValue();
      if (value !== lastTarget) {
        throw new Error(`Recall input value ${value} did not match target ${lastTarget}`);
      }
      if (slowFlow) {
        await page.waitForTimeout(1600);
      }
    }

    if (url.includes("/recruiter-exit")) {
      await page.screenshot({ path: path.join(screenshotDir, "04-completion.png") });
      await page.waitForTimeout(completionDelayMs);
      break;
    }

    await clickContinue(page);
  }

  if (!page.url().includes("/recruiter-exit")) {
    throw new Error(`Participant did not reach recruiter-exit; final URL was ${page.url()}`);
  }
  if (trialLog.length !== 10) {
    throw new Error(`Expected 10 study trials, observed ${trialLog.length}`);
  }
  fs.writeFileSync(
    path.join(evidenceDir, "participant-flow-log.json"),
    JSON.stringify({ completed: true, trials: trialLog }, null, 2) + "\n"
  );
  fs.writeFileSync(
    path.join(screenshotDir, "manifest.json"),
    JSON.stringify(screenshotManifest, null, 2) + "\n"
  );

  await browser.close();
})();
