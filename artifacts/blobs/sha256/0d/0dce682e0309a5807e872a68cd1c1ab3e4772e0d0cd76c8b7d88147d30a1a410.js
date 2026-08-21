const { test, expect, chromium } = require("@playwright/test");
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const participantUrl = process.env.PARTICIPANT_URL;
if (!participantUrl) {
  throw new Error("PARTICIPANT_URL must point to a PsyNet /ad URL.");
}

const experimentDir = path.resolve(__dirname, "..");
const attemptDir = path.resolve(experimentDir, "../..");
const evidenceDir = path.join(attemptDir, "evidence");
const screenshotDir = path.join(evidenceDir, "screenshots");
const videoDir = path.join(evidenceDir, "playwright-video");

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

async function clickPrimaryButton(page) {
  const buttons = page.locator("button:visible, input[type=submit]:visible, a.btn:visible");
  await expect(buttons.first()).toBeVisible({ timeout: 15000 });
  await buttons.first().click();
}

async function acceptConsentIfPresent(page) {
  const body = await page.locator("body").innerText();
  if (/consent/i.test(body)) {
    const checkboxes = await page.locator("input[type=checkbox]:visible").all();
    for (const checkbox of checkboxes) {
      if (!(await checkbox.isChecked())) {
        await checkbox.check({ force: true });
      }
    }
    const yesRadio = page.locator("input[type=radio][value='yes'], input[type=radio][value='true']").first();
    if (await yesRadio.count()) {
      await yesRadio.check({ force: true });
    }
  }
}

function extractDigitTarget(text) {
  const matches = text.match(/\b\d{2,20}\b/g) || [];
  return matches.sort((a, b) => b.length - a.length)[0] || null;
}

test("participant completes adaptive memory flow", async () => {
  ensureDir(screenshotDir);
  ensureDir(videoDir);

  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || "/usr/local/bin/google-chrome",
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();
  const recalledLengths = [];
  let target = null;

  await page.goto(participantUrl, { waitUntil: "domcontentloaded" });
  await page.screenshot({ path: path.join(screenshotDir, "01-ad-page.png"), fullPage: true });

  for (let step = 0; step < 80; step += 1) {
    if (page.url().includes("/recruiter-exit")) {
      break;
    }

    await acceptConsentIfPresent(page);
    const body = await page.locator("body").innerText();
    const candidateTarget = extractDigitTarget(body);
    if (candidateTarget) {
      target = candidateTarget;
      if (recalledLengths.length === 0) {
        await page.screenshot({ path: path.join(screenshotDir, "02-study-page.png"), fullPage: true });
      }
    }

    const textInput = page.locator("input[type=text]:visible, textarea:visible").first();
    if ((await textInput.count()) && target) {
      await textInput.fill(target);
      recalledLengths.push(target.length);
      if (recalledLengths.length === 1) {
        await page.screenshot({ path: path.join(screenshotDir, "03-recall-page.png"), fullPage: true });
      }
      target = null;
    }

    await clickPrimaryButton(page);
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await page.waitForTimeout(250);
  }

  await expect(page).toHaveURL(/recruiter-exit/, { timeout: 15000 });
  await page.screenshot({ path: path.join(screenshotDir, "04-completion.png"), fullPage: true });
  expect(recalledLengths).toHaveLength(10);
  expect(Math.min(...recalledLengths)).toBeGreaterThanOrEqual(2);
  expect(Math.max(...recalledLengths)).toBeLessThanOrEqual(20);

  await context.close();
  await browser.close();

  const webm = fs.readdirSync(videoDir).find((name) => name.endsWith(".webm"));
  if (!webm) {
    throw new Error("Playwright did not create a video artifact.");
  }
  const inputVideo = path.join(videoDir, webm);
  const outputVideo = path.join(evidenceDir, "participant.mp4");
  execFileSync("ffmpeg", [
    "-y",
    "-i",
    inputVideo,
    "-vf",
    "scale='trunc(min(1,min(1280/iw,720/ih))*iw/2)*2':'trunc(min(1,min(1280/iw,720/ih))*ih/2)*2',fps=15",
    "-c:v",
    "libx264",
    "-preset",
    "medium",
    "-crf",
    "32",
    "-pix_fmt",
    "yuv420p",
    "-an",
    "-movflags",
    "+faststart",
    outputVideo,
  ]);
});
