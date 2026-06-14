const { chromium, expect } = require("@playwright/test");
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const BASE_URL = process.env.PSYNET_BASE_URL || "http://127.0.0.1:5000";
const DASHBOARD_URL = process.env.PSYNET_DASHBOARD_URL;
const EVIDENCE_DIR = path.resolve(__dirname, "../../../evidence");
const SCREENSHOT_DIR = path.join(EVIDENCE_DIR, "screenshots");
const VIDEO_TMP_DIR = path.join(EVIDENCE_DIR, "playwright-video");

async function clickVisible(page, selector) {
  const locator = page.locator(selector).first();
  await expect(locator).toBeVisible({ timeout: 10000 });
  await locator.click();
}

async function waitForEnabledResponse(page) {
  await page.waitForFunction(() => {
    return [...document.querySelectorAll("button.response")].some(
      (button) => !button.disabled && /^[1-5]$/.test(button.id)
    );
  });
  return page.locator("button.response:not([disabled])").filter({ hasText: /^[1-5]$/ });
}

async function saveDashboardMonitor(page) {
  if (!DASHBOARD_URL) {
    throw new Error("PSYNET_DASHBOARD_URL must be set to capture monitor.html");
  }
  await page.goto(DASHBOARD_URL, { waitUntil: "networkidle" });
  const html = await page.content();
  fs.writeFileSync(path.join(EVIDENCE_DIR, "monitor.html"), html);
}

(async () => {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  fs.mkdirSync(VIDEO_TMP_DIR, { recursive: true });
  for (const name of fs.readdirSync(VIDEO_TMP_DIR)) {
    fs.rmSync(path.join(VIDEO_TMP_DIR, name), { recursive: true, force: true });
  }

  const browser = await chromium.launch({
    executablePath: "/usr/local/bin/google-chrome",
    headless: true,
    args: ["--no-sandbox"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: VIDEO_TMP_DIR, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();

  await page.goto(`${BASE_URL}/ad?generate_tokens=true&recruiter=hotair`, {
    waitUntil: "networkidle",
  });
  await clickVisible(page, "#begin-button");
  await clickVisible(page, "#consent");

  await expect(page.locator("body")).toContainText("numbered colored circles");
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "01_instructions.png"),
    fullPage: true,
  });
  await clickVisible(page, "#next-button");

  let trialCount = 0;
  while (!page.url().includes("/recruiter-exit")) {
    if ((await page.locator("button.response").filter({ hasText: /^[1-5]$/ }).count()) > 0) {
      trialCount += 1;
      if (trialCount === 1) {
        await page.waitForTimeout(850);
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, "02_numbered_array.png"),
          fullPage: true,
        });
        await page.waitForTimeout(1200);
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, "03_probe_response.png"),
          fullPage: true,
        });
      }
      const enabled = await waitForEnabledResponse(page);
      await enabled.first().click();
      await page.waitForTimeout(2200);
    } else if ((await page.locator("#next-button:visible:not([disabled])").count()) > 0) {
      await page.locator("#next-button:visible:not([disabled])").click();
      await page.waitForTimeout(250);
    } else if ((await page.locator("button.push-button:visible").count()) > 0) {
      await page.locator("button.push-button:visible").first().click();
      await page.waitForTimeout(500);
    } else {
      await page.waitForTimeout(500);
    }
  }

  if (trialCount !== 10) {
    throw new Error(`Expected 10 participant trials, completed ${trialCount}`);
  }
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "04_completion.png"),
    fullPage: true,
  });

  await saveDashboardMonitor(page);
  await context.close();
  await browser.close();

  const videoFiles = fs
    .readdirSync(VIDEO_TMP_DIR)
    .filter((name) => name.endsWith(".webm"));
  if (videoFiles.length !== 1) {
    throw new Error(`Expected one Playwright video, found ${videoFiles.length}`);
  }
  const rawVideo = path.join(VIDEO_TMP_DIR, videoFiles[0]);
  const finalVideo = path.join(EVIDENCE_DIR, "participant.mp4");
  execFileSync("ffmpeg", [
    "-y",
    "-i",
    rawVideo,
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
    "-movflags",
    "+faststart",
    finalVideo,
  ]);

  fs.writeFileSync(
    path.join(SCREENSHOT_DIR, "manifest.json"),
    JSON.stringify(
      {
        captions: {
          "01_instructions.png": "Participant instructions explain numbered arrays, probe matching, and keyboard or mouse responses.",
          "02_numbered_array.png": "Timed numbered colored-circle array around fixation.",
          "03_probe_response.png": "Probe display with numbered response buttons after the blank delay.",
          "04_completion.png": "Participant flow reached the recruiter exit page after ten trials.",
        },
      },
      null,
      2
    ) + "\n"
  );
  console.log(`Completed ${trialCount} trials and wrote participant evidence.`);
})();
