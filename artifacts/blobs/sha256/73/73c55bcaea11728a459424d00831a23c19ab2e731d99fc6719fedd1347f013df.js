const fs = require("fs");
const path = require("path");
const { test, expect, chromium } = require("@playwright/test");

const baseUrl = process.env.PSYNET_BASE_URL || "http://127.0.0.1:5000";
const evidenceDir = path.resolve(__dirname, "../../../evidence");
const screenshotDir = path.join(evidenceDir, "screenshots");
const videoDir = path.join(evidenceDir, "playwright-video");

async function dismissResume(page) {
  const resume = page.getByRole("button", { name: /resume|ready/i });
  if (await resume.isVisible().catch(() => false)) {
    await resume.click();
    await page.waitForTimeout(300);
  }
}

async function clickVisibleContinue(page) {
  await dismissResume(page);
  const candidates = [
    page.getByRole("button", { name: /next/i }),
    page.getByRole("button", { name: /continue/i }),
    page.getByRole("button", { name: /begin/i }),
    page.getByRole("button", { name: /start/i }),
    page.getByRole("button", { name: /agree/i }),
    page.getByRole("link", { name: /continue|start|participate/i }),
  ];
  for (const candidate of candidates) {
    if (await candidate.first().isVisible().catch(() => false)) {
      await candidate.first().click();
      await page.waitForTimeout(500);
      return true;
    }
  }
  const nextButton = page.locator("#next-button");
  if (await nextButton.isVisible().catch(() => false)) {
    await nextButton.click();
    await page.waitForTimeout(500);
    return true;
  }
  return false;
}

async function reachFirstTask(page) {
  for (let i = 0; i < 25; i++) {
    if (await page.locator("#guidance").isVisible().catch(() => false)) {
      return;
    }
    const clicked = await clickVisibleContinue(page);
    if (!clicked) {
      await page.waitForTimeout(500);
    }
  }
  throw new Error("Could not reach first SVG task page.");
}

async function submitIteration(page, options) {
  await dismissResume(page);
  await expect(page.locator("#guidance")).toBeVisible();
  if (options.guidance) {
    await page.locator("#guidance").fill(options.guidance);
  }
  await page.getByRole("button", { name: "Generate SVG candidate" }).click();
  await expect(page.locator("#candidate-preview svg")).toBeVisible();
  await page.waitForTimeout(1200);
  if (options.screenshot) {
    await page.screenshot({ path: path.join(screenshotDir, options.screenshot), fullPage: false });
  }
  if (options.choice === "previous") {
    await page.locator("#choose-previous").check();
  } else if (options.choice === "candidate") {
    await page.locator("#choose-candidate").check();
  }
  if (options.reason) {
    await page.locator("#selector-reasoning").fill(options.reason);
  }
  await page.waitForTimeout(800);
  await page.getByRole("button", { name: "Submit iteration" }).click();
  await page.waitForTimeout(1000);
}

test("participant completes collaborative SVG flow", async () => {
  fs.mkdirSync(screenshotDir, { recursive: true });
  fs.mkdirSync(videoDir, { recursive: true });

  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();

  await page.goto(`${baseUrl}/ad?generate_tokens=true&recruiter=hotair`, {
    waitUntil: "domcontentloaded",
  });
  await reachFirstTask(page);
  await page.screenshot({ path: path.join(screenshotDir, "playwright-01-first-task.png"), fullPage: false });

  await submitIteration(page, {
    guidance: "Draw a front-facing cat with triangular ears, dark eyes, a round face, whiskers, and warm colors.",
    screenshot: "playwright-02-iteration-1-generated.png",
    choice: "candidate",
  });

  await expect(page.locator("text=Iteration 2")).toBeVisible();
  await submitIteration(page, {
    screenshot: "playwright-03-iteration-2-selector.png",
    choice: "previous",
    reason: "The previous best has a warmer cat-like color match.",
  });

  await expect(page.locator("text=Iteration 3")).toBeVisible();
  await submitIteration(page, {
    screenshot: "playwright-04-iteration-3-ai-led.png",
    choice: "candidate",
  });

  for (let i = 0; i < 10; i++) {
    if (await page.getByText("Independent similarity rating").isVisible().catch(() => false)) {
      break;
    }
    await clickVisibleContinue(page);
  }
  await expect(page.getByText("Independent similarity rating")).toBeVisible();
  await expect(page.getByText("condition", { exact: false })).not.toBeVisible();
  await page.screenshot({ path: path.join(screenshotDir, "playwright-05-evaluator-rating.png"), fullPage: false });

  const rating = page.locator('input[type="radio"][value="4"]').first();
  await rating.check({ force: true });
  await page.waitForTimeout(800);
  await clickVisibleContinue(page);
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(screenshotDir, "playwright-06-completion.png"), fullPage: false });

  await context.close();
  await browser.close();

  const videos = fs.readdirSync(videoDir).filter((file) => file.endsWith(".webm"));
  if (videos.length === 0) {
    throw new Error("Playwright did not save a participant video.");
  }
  const newest = videos
    .map((file) => path.join(videoDir, file))
    .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0];
  fs.copyFileSync(newest, path.join(evidenceDir, "participant_playwright.webm"));
});
