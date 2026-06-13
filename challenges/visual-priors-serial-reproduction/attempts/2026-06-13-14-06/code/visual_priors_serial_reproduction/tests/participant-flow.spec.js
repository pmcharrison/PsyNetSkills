const { test, expect, chromium } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const participantUrl =
  process.env.PARTICIPANT_URL ||
  "http://localhost:5000/ad?recruiter=hotair&generate_tokens=1&mode=debug";
const evidenceDir = path.resolve(process.env.EVIDENCE_DIR || "../../evidence");
const screenshotsDir = path.join(evidenceDir, "screenshots");
const videoDir = path.join(evidenceDir, "playwright-video");

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

async function clickContinue(page) {
  const selectors = [
    "button:has-text('Start')",
    "button:has-text('Begin')",
    "button:has-text('Continue')",
    "button:has-text('Next')",
    "button:has-text('I agree')",
    "button:has-text('Finish')",
    "button.push-button",
    "a.btn",
  ];
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    if ((await locator.count()) > 0 && (await locator.isVisible())) {
      await locator.click();
      return true;
    }
  }
  return false;
}

async function waitForMemoryPhase(page, phaseText) {
  await expect(page.locator("#memory-task")).toBeVisible({ timeout: 15000 });
  await expect(page.locator("#phase-title")).toContainText(phaseText, {
    timeout: 8000,
  });
}

async function advanceToMemoryTask(page) {
  for (let i = 0; i < 12; i += 1) {
    if (await page.locator("#memory-task").first().isVisible()) {
      return;
    }
    if (!(await clickContinue(page))) {
      await page.waitForTimeout(500);
    }
  }
  await expect(page.locator("#memory-task")).toBeVisible({ timeout: 15000 });
}

async function respondToMemoryTrial(page) {
  await waitForMemoryPhase(page, "Reproduce");
  await page.locator("#memory-canvas").evaluate((svg) => {
    const rect = svg.getBoundingClientRect();
    svg.dispatchEvent(
      new MouseEvent("click", {
        bubbles: true,
        clientX: rect.left + rect.width / 2,
        clientY: rect.top + rect.height / 2,
      }),
    );
  });
  await expect(page.locator("#feedback")).toContainText(/accurate/i);
}

async function submitMemoryTrial(page) {
  await page.locator("#submit-response").evaluate((button) => button.click());
}

test("participant completes representative serial reproduction flow", async () => {
  ensureDir(screenshotsDir);
  ensureDir(videoDir);

  const browser = await chromium.launch({
    executablePath: "/usr/local/bin/google-chrome",
    headless: true,
    args: ["--no-sandbox"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();

  await page.goto(participantUrl);

  for (let i = 0; i < 8; i += 1) {
    if (await page.locator("text=In this experiment").first().isVisible()) {
      break;
    }
    if (await page.locator("#memory-task").first().isVisible()) {
      break;
    }
    if (!(await clickContinue(page))) {
      await page.waitForTimeout(500);
    }
  }

  await expect(page.locator("text=In this experiment").first()).toBeVisible({
    timeout: 15000,
  });
  await page.screenshot({
    path: path.join(screenshotsDir, "01_instructions.png"),
    fullPage: true,
  });
  await clickContinue(page);

  await advanceToMemoryTask(page);
  await waitForMemoryPhase(page, "Remember");
  await page.screenshot({
    path: path.join(screenshotsDir, "02_stimulus_display.png"),
    fullPage: true,
  });

  await respondToMemoryTrial(page);
  await page.screenshot({
    path: path.join(screenshotsDir, "03_response_feedback.png"),
    fullPage: true,
  });
  await submitMemoryTrial(page);

  let experimentalScreenshotTaken = false;
  for (let step = 0; step < 80; step += 1) {
    if (page.url().includes("/recruiter-exit")) {
      break;
    }
    if (await page.locator("#memory-task").first().isVisible()) {
      await respondToMemoryTrial(page);
      if (!experimentalScreenshotTaken) {
        await page.screenshot({
          path: path.join(screenshotsDir, "04_experimental_feedback.png"),
          fullPage: true,
        });
        experimentalScreenshotTaken = true;
      }
      await submitMemoryTrial(page);
    } else if (!(await clickContinue(page))) {
      await page.waitForTimeout(500);
    }
  }

  await expect(page).toHaveURL(/recruiter-exit/, { timeout: 30000 });

  const manifest = {
    captions: {
      "01_instructions.png": "Participant instructions for the dot-location memory task.",
      "02_stimulus_display.png": "Timed stimulus display with a dot inside the outline.",
      "03_response_feedback.png": "Practice response screen showing click feedback.",
      "04_experimental_feedback.png": "Experimental chain trial response screen showing feedback.",
    },
  };
  fs.writeFileSync(
    path.join(screenshotsDir, "manifest.json"),
    JSON.stringify(manifest, null, 2),
  );

  const video = page.video();
  await context.close();
  await browser.close();
  if (video) {
    await video.saveAs(path.join(evidenceDir, "participant.webm"));
  }
});
