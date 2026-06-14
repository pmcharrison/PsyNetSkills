const fs = require("fs");
const path = require("path");
const { chromium, expect } = require("@playwright/test");

const baseUrl = process.env.BASE_URL || "http://127.0.0.1:5000";
const locale = process.env.LOCALE || "en";
const evidenceDir = process.env.EVIDENCE_DIR || path.resolve(__dirname, "../../../evidence");
const screenshotDir = path.join(evidenceDir, "screenshots");
const videoDir = path.join(evidenceDir, "raw-videos", locale);

function participantUrl() {
  const suffix = `${locale}-${Date.now()}`;
  const url = new URL("/ad", baseUrl);
  url.searchParams.set("worker_id", `worker-${suffix}`);
  url.searchParams.set("assignment_id", `assignment-${suffix}`);
  url.searchParams.set("hit_id", "autocog-demo");
  return url.toString();
}

async function clickSubmit(page) {
  await page.locator("button.submit:visible:not([disabled])").first().click();
  await page.waitForTimeout(250);
}

async function run() {
  fs.mkdirSync(screenshotDir, { recursive: true });
  fs.mkdirSync(videoDir, { recursive: true });
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
    args: ["--no-sandbox"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();
  await page.goto(participantUrl(), { waitUntil: "domcontentloaded" });

  await expect(page.getByRole("button").first()).toBeVisible();
  await page.screenshot({ path: path.join(screenshotDir, `${locale}-01-ad.png`), fullPage: true });
  await page.getByRole("button").first().click();

  await page.waitForURL(/\/consent/);
  await page.getByRole("button").first().click();

  await page.waitForURL(/\/timeline/);
  await expect(page.locator("body")).toContainText(locale === "en" ? "Welcome" : /.+/);
  await page.screenshot({ path: path.join(screenshotDir, `${locale}-02-welcome.png`), fullPage: true });
  await clickSubmit(page);

  await page.screenshot({ path: path.join(screenshotDir, `${locale}-03-instructions.png`), fullPage: true });
  await clickSubmit(page);

  await expect(page.locator("table").first()).toBeVisible();
  if ((await page.locator("table:visible").count()) < 2) {
    throw new Error(`Expected two visible option tables for locale ${locale}`);
  }
  await page.screenshot({ path: path.join(screenshotDir, `${locale}-04-choice.png`), fullPage: true });

  let choices = 0;
  while (!page.url().includes("recruiter-exit")) {
    const choiceButtons = page.locator(
      "button.push-button:visible:not([disabled])#option_a, button.push-button:visible:not([disabled])#option_b"
    );
    if ((await choiceButtons.count()) > 0) {
      await choiceButtons.first().click();
      choices += 1;
    } else if ((await page.locator("button.submit:visible:not([disabled])").count()) > 0) {
      await clickSubmit(page);
    } else {
      await page.waitForTimeout(250);
    }
    if (choices > 55) {
      throw new Error(`Too many choices without completion for locale ${locale}`);
    }
  }

  if (choices !== 50) {
    throw new Error(`Expected 50 choices, got ${choices}`);
  }
  await page.screenshot({ path: path.join(screenshotDir, `${locale}-05-complete.png`), fullPage: true });
  const video = await page.video().path();
  await context.close();
  await browser.close();
  const target = path.join(videoDir, `${locale}.webm`);
  fs.renameSync(video, target);
  console.log(JSON.stringify({ locale, choices, video: target }));
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});

