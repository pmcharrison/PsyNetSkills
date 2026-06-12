const fs = require("fs");
const path = require("path");
const { chromium, expect, test } = require("@playwright/test");

const participantUrl = process.env.PARTICIPANT_URL;
const evidenceDir = process.env.EVIDENCE_DIR
  ? path.resolve(process.env.EVIDENCE_DIR)
  : path.resolve(__dirname, "../../../evidence");
const screenshotDir = path.join(evidenceDir, "screenshots");
const videoDir = path.join(evidenceDir, "playwright-video");
const chromeExecutable =
  process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || "/usr/local/bin/google-chrome";

async function clickMainNext(page) {
  await page.getByRole("button", { name: "Next" }).first().click();
}

async function rateColor(page, color, rating, screenshotName) {
  await expect(page.getByText("How pleasant is this color?")).toBeVisible();
  await expect(page.getByText(color, { exact: true })).toBeVisible();
  await page.screenshot({ path: path.join(screenshotDir, screenshotName), fullPage: true });
  await page.getByText(String(rating), { exact: true }).click();
  await clickMainNext(page);
}

test("participant rates red, green, and blue in order", async () => {
  if (!participantUrl) {
    throw new Error("Set PARTICIPANT_URL to the PsyNet ad page URL.");
  }

  fs.mkdirSync(screenshotDir, { recursive: true });
  fs.mkdirSync(videoDir, { recursive: true });

  const browser = await chromium.launch({
    executablePath: chromeExecutable,
    headless: true,
    args: ["--no-sandbox"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();

  await page.goto(participantUrl);
  await expect(page.getByRole("button", { name: "Begin Experiment" })).toBeVisible();
  await page.screenshot({
    path: path.join(screenshotDir, "01-ad-page.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Begin Experiment" }).click();

  await expect(page.getByRole("button", { name: "Next" }).first()).toBeVisible();
  await page.screenshot({
    path: path.join(screenshotDir, "02-consent-page.png"),
    fullPage: true,
  });
  await clickMainNext(page);

  await expect(page.getByText("Welcome! In this short experiment")).toBeVisible();
  await page.screenshot({
    path: path.join(screenshotDir, "03-welcome-page.png"),
    fullPage: true,
  });
  await clickMainNext(page);

  await rateColor(page, "Red", 5, "04-red-rating.png");
  await rateColor(page, "Green", 6, "05-green-rating.png");
  await rateColor(page, "Blue", 4, "06-blue-rating.png");

  await expect(page.getByText("Thank you for rating the colors!")).toBeVisible();
  await page.screenshot({
    path: path.join(screenshotDir, "07-thank-you-page.png"),
    fullPage: true,
  });

  const video = page.video();
  await context.close();
  await browser.close();
  await video.saveAs(path.join(evidenceDir, "participant.webm"));

  const manifest = {
    captions: {
      "screenshots/01-ad-page.png": "PsyNet recruitment page with the Begin Experiment button.",
      "screenshots/02-consent-page.png": "Local debug consent page before entering the task.",
      "screenshots/03-welcome-page.png": "Welcome page explaining the short color-rating task.",
      "screenshots/04-red-rating.png": "First rating trial showing the red color swatch.",
      "screenshots/05-green-rating.png": "Second rating trial showing the green color swatch.",
      "screenshots/06-blue-rating.png": "Third rating trial showing the blue color swatch.",
      "screenshots/07-thank-you-page.png": "Thank-you page after all three ratings are submitted.",
    },
  };
  fs.writeFileSync(
    path.join(screenshotDir, "manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
  );
});
