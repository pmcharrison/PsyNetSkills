const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

const participantUrl =
  process.env.PARTICIPANT_URL ||
  "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair";
const evidenceDir = path.resolve(process.cwd(), "../../evidence");
const screenshotDir = path.join(evidenceDir, "screenshots");

async function clickButton(page, name) {
  await page.getByRole("button", { name }).first().click();
  await page.waitForTimeout(900);
}

async function answerPrescreen(page, screenshotIndex) {
  await expect(page.getByText("Which tone did you hear?")).toBeVisible();
  await page.waitForFunction(() =>
    Array.from(document.querySelectorAll("button")).some(
      (button) => button.innerText.trim() === "Low" && !button.disabled,
    ),
  );

  if (screenshotIndex === 0) {
    await page.screenshot({
      path: path.join(screenshotDir, "02-audio-prescreen.png"),
      fullPage: true,
    });
  }

  const html = await page.content();
  const nodeId = Number(html.match(/node_(\d+)__stimulus/)?.[1]);
  const answer = { 1: "Low", 2: "Middle", 3: "High" }[nodeId];
  if (!answer) {
    throw new Error(`Could not infer prescreen answer from node id ${nodeId}`);
  }
  await clickButton(page, answer);
}

async function advancePromptIfNeeded(page) {
  await page.evaluate(() => window.psynet?.trial?.registerEvent("promptEnd"));
  await page.waitForTimeout(300);
}

async function answerRating(page, index) {
  await expect(page.getByText(/Listen to the 10-second excerpt/)).toBeVisible();
  if (index === 0) {
    await page.waitForTimeout(11_000);
    await advancePromptIfNeeded(page);
    await page.screenshot({
      path: path.join(screenshotDir, "03-song-rating.png"),
      fullPage: true,
    });
  } else {
    await advancePromptIfNeeded(page);
  }

  const rating = page.getByLabel("5", { exact: true });
  if (await rating.count()) {
    await rating.first().check({ force: true });
  } else {
    await page.getByText("5", { exact: true }).first().click();
  }
  await page.locator("button.submit").first().click({ force: true });
  await page.waitForTimeout(350);
}

test("participant completes prescreen and song-rating flow", async ({ browser }) => {
  test.setTimeout(180_000);
  fs.mkdirSync(screenshotDir, { recursive: true });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: path.join(evidenceDir, "playwright-video"), size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();

  await page.goto(participantUrl, { waitUntil: "domcontentloaded" });
  await clickButton(page, "Begin Experiment");
  await clickButton(page, "Next");

  await expect(page.getByText("Welcome. In this experiment")).toBeVisible();
  await page.screenshot({
    path: path.join(screenshotDir, "01-welcome.png"),
    fullPage: true,
  });
  await clickButton(page, "Next");
  await clickButton(page, "Next");

  for (let i = 0; i < 3; i += 1) {
    await answerPrescreen(page, i);
  }

  await expect(page.getByText("Audio check passed")).toBeVisible();
  await clickButton(page, "Next");

  for (let i = 0; i < 30; i += 1) {
    await answerRating(page, i);
  }

  await expect(page.getByText("Thank you for completing")).toBeVisible();
  await page.screenshot({
    path: path.join(screenshotDir, "04-completion.png"),
    fullPage: true,
  });

  fs.writeFileSync(
    path.join(screenshotDir, "manifest.json"),
    JSON.stringify(
      {
        captions: {
          "01-welcome.png": "Welcome page describing the audio check and 1-9 song-rating task.",
          "02-audio-prescreen.png": "Audio-hearing prescreen after playback has enabled the answer buttons.",
          "03-song-rating.png": "First S3-backed 10-second song excerpt ready for a 1-9 liking rating.",
          "04-completion.png": "Participant completion page after the scripted 30-trial flow.",
        },
      },
      null,
      2,
    ),
  );

  await context.close();
});
