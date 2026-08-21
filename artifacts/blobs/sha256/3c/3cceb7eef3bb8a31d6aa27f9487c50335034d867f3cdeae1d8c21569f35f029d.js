const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const evidenceDir = path.resolve(__dirname, "../../../evidence");
const screenshotsDir = path.join(evidenceDir, "screenshots");

async function screenshot(page, filename) {
  await page.screenshot({
    path: path.join(screenshotsDir, filename),
    fullPage: true,
  });
}

test("participant rates red, green, and blue in order", async ({ page }) => {
  fs.mkdirSync(screenshotsDir, { recursive: true });

  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(
    "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair",
    { waitUntil: "domcontentloaded" }
  );

  await expect(page.getByText("Begin Experiment")).toBeVisible();
  await page.getByText("Begin Experiment").click();

  await expect(page.getByRole("button", { name: "Next" })).toBeVisible();
  await page.getByRole("button", { name: "Next" }).click();

  await expect(page.getByText("Welcome!")).toBeVisible();
  await screenshot(page, "01-welcome.png");
  await page.getByRole("button", { name: "Next" }).click();

  const ratings = [
    ["red", "3", "02-red-trial.png"],
    ["green", "5", "03-green-trial.png"],
    ["blue", "7", "04-blue-trial.png"],
  ];

  for (const [color, rating, filename] of ratings) {
    await expect(
      page.getByText(`How pleasant is this color? (${color})`)
    ).toBeVisible();
    await expect(page.getByText("Not at all pleasant")).toBeVisible();
    await expect(page.getByText("Very pleasant")).toBeVisible();
    await screenshot(page, filename);
    await page.getByText(rating, { exact: true }).click();
    await page.getByRole("button", { name: "Next" }).click();
  }

  await expect(page.getByText("Thank you for rating the colors!")).toBeVisible();
  await screenshot(page, "05-thank-you.png");
});
