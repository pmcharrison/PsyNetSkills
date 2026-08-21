const { test, expect } = require("@playwright/test");
const path = require("path");

const attemptRoot = path.resolve(__dirname, "../../..");
const evidenceDir = path.join(attemptRoot, "evidence");
const screenshotsDir = path.join(evidenceDir, "screenshots");
const videoDir = path.join(evidenceDir, "video-recording");
const baseUrl = process.env.PSYNET_BASE_URL || "http://127.0.0.1:5000";

async function clickNext(page) {
  await page.waitForTimeout(400);
  await page.locator("#next-button").click();
  await page.waitForLoadState("networkidle");
}

async function rateCurrentColor(page, colorName, screenshotName) {
  await expect(page.getByText("How pleasant is this color?")).toBeVisible();
  await expect(page.getByText(`Please rate the pleasantness of ${colorName}.`)).toBeVisible();
  await page.screenshot({ path: path.join(screenshotsDir, screenshotName), fullPage: true });
  await page.waitForTimeout(700);
  await page.locator('input[name="rating"][value="4"]').check({ force: true });
  await page.waitForTimeout(300);
  await clickNext(page);
}

test.use({
  channel: "chrome",
  headless: true,
  viewport: { width: 1280, height: 720 },
  video: "on",
});

test("participant rates red, green, and blue", async ({ page }, testInfo) => {
  await page.context().tracing.start({ screenshots: true, snapshots: true });

  await page.goto(`${baseUrl}/ad?generate_tokens=true&recruiter=hotair`);
  await expect(page.locator("#begin-button")).toBeVisible();
  await page.locator("#begin-button").click();
  await page.waitForLoadState("networkidle");

  await expect(page.locator("#consent")).toBeVisible();
  await page.locator("#consent").click();
  await page.waitForLoadState("networkidle");

  await expect(
    page.getByText("Welcome! In this short experiment you will rate three primary colors for pleasantness.")
  ).toBeVisible();
  await page.screenshot({ path: path.join(screenshotsDir, "01-welcome.png"), fullPage: true });
  await page.waitForTimeout(700);
  await clickNext(page);

  await rateCurrentColor(page, "red", "02-red-rating.png");
  await rateCurrentColor(page, "green", "03-green-rating.png");
  await rateCurrentColor(page, "blue", "04-blue-rating.png");

  await expect(page.getByText("Thank you for rating the colors!")).toBeVisible();
  await page.screenshot({ path: path.join(screenshotsDir, "05-thank-you.png"), fullPage: true });
  await page.waitForTimeout(700);
  await clickNext(page);

  await expect(page.getByText(/Reward|complete|finished|submitted/i)).toBeVisible();
  await page.screenshot({ path: path.join(screenshotsDir, "06-completion.png"), fullPage: true });
  await page.waitForTimeout(700);

  await page.context().tracing.stop({ path: path.join(evidenceDir, "participant-flow-trace.zip") });
  const video = page.video();
  if (video) {
    const videoPath = await video.path();
    testInfo.attachments.push({ name: "participant-video", path: videoPath, contentType: "video/webm" });
  }
});
