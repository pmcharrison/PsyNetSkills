const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

const participantUrl =
  process.env.PARTICIPANT_URL ||
  "http://localhost:5000/ad?recruiter=hotair&generate_tokens=1&mode=debug";

const evidenceDir = path.resolve(__dirname, "../../../evidence");
const screenshotsDir = path.join(evidenceDir, "screenshots");

test.use({ channel: "chrome" });

async function saveScreenshot(page, name) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  await page.screenshot({ path: path.join(screenshotsDir, name), fullPage: true });
}

async function clickNext(page) {
  await page.getByRole("button", { name: /next/i }).click();
}

test("participant completes the animal choice flow", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(participantUrl);

  await expect(page.getByText(/Begin Experiment/i)).toBeVisible();
  await saveScreenshot(page, "01-begin.png");
  await page.getByText(/Begin Experiment/i).click();

  await expect(page.getByRole("heading", { name: /Animal choices/i })).toBeVisible();
  await saveScreenshot(page, "02-welcome.png");
  await clickNext(page);

  await expect(page.getByText(/There are only two questions/i)).toBeVisible();
  await expect(page.getByText(/cat, dog, and bird/i)).toBeVisible();
  await saveScreenshot(page, "03-instructions.png");
  await clickNext(page);

  await expect(page.getByText(/Question 1 of 2/i)).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /Which animal would you most like to have as a companion/i,
    })
  ).toBeVisible();
  await expect(page.getByRole("button", { name: /Cat/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /Dog/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /Bird/i })).toBeVisible();
  await saveScreenshot(page, "04-trial-companion.png");
  await page.getByRole("button", { name: /Dog/i }).click();

  await expect(page.getByText(/Question 2 of 2/i)).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /Which animal do you think is most respected in your community/i,
    })
  ).toBeVisible();
  await saveScreenshot(page, "05-trial-community-respect.png");
  await page.getByRole("button", { name: /Cat/i }).click();

  await expect(page.getByRole("heading", { name: /Thank you/i })).toBeVisible();
  await expect(
    page.getByText(/You have completed the animal choice experiment/i)
  ).toBeVisible();
  await saveScreenshot(page, "06-completion.png");

  fs.writeFileSync(
    path.join(screenshotsDir, "manifest.json"),
    JSON.stringify(
      {
        captions: {
          "01-begin.png": "Debug landing page before starting the participant flow.",
          "02-welcome.png": "Welcome page with the animal choice experiment title.",
          "03-instructions.png": "Instructions explaining two questions and three animal choices.",
          "04-trial-companion.png": "First trial with randomized animal buttons and keyboard hints.",
          "05-trial-community-respect.png": "Second trial with randomized animal buttons and keyboard hints.",
          "06-completion.png": "Thank-you page after exactly two choice trials.",
        },
      },
      null,
      2
    )
  );
});
