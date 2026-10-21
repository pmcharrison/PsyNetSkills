const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

const evidenceDir = path.resolve(__dirname, "../../../evidence");
const screenshotsDir = path.join(evidenceDir, "screenshots");

async function saveScreenshot(page, filename) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  await page.screenshot({
    path: path.join(screenshotsDir, filename),
    fullPage: false,
  });
}

async function clickVisible(page, labels) {
  for (const label of labels) {
    const pattern = new RegExp(label, "i");
    const control = page
      .getByRole("button", { name: pattern })
      .or(page.getByRole("link", { name: pattern }))
      .first();
    if ((await control.count()) > 0 && (await control.isVisible())) {
      await control.click();
      return true;
    }
  }
  return false;
}

async function advanceToInstructions(page) {
  for (let step = 0; step < 20; step += 1) {
    if (await page.getByText("Color matching task").isVisible()) {
      return;
    }
    const clicked = await clickVisible(page, [
      "accept",
      "agree",
      "consent",
      "begin",
      "start",
      "continue",
      "next",
      "participate",
    ]);
    if (!clicked) {
      await page.waitForTimeout(250);
    }
  }
  await expect(page.getByText("Color matching task")).toBeVisible();
}

test("participant completes the visual discrimination flow with keyboard responses", async ({
  page,
}) => {
  const participantUrl = process.env.PARTICIPANT_URL;
  if (!participantUrl) {
    throw new Error("Set PARTICIPANT_URL to the PsyNet debug-local ad URL.");
  }

  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(participantUrl);
  await advanceToInstructions(page);

  await saveScreenshot(page, "01-instructions.png");
  await clickVisible(page, ["next", "continue", "start"]);

  for (let trialIndex = 0; trialIndex < 10; trialIndex += 1) {
    const sameButton = page.locator("button#same");
    const differentButton = page.locator("button#different");

    await sameButton.waitFor({ state: "attached" });
    await expect(sameButton).toBeDisabled();
    await expect(differentButton).toBeDisabled();

    if (trialIndex === 0) {
      await saveScreenshot(page, "02-trial-response-disabled.png");
    }

    await expect(sameButton).toBeEnabled({ timeout: 5000 });
    await expect(differentButton).toBeEnabled();

    if (trialIndex === 0) {
      await saveScreenshot(page, "03-trial-response-enabled.png");
    }

    await page.keyboard.press(trialIndex % 2 === 0 ? "KeyF" : "KeyJ");
  }

  await expect(page.getByText("You have completed the color matching task.")).toBeVisible({
    timeout: 10000,
  });
  await saveScreenshot(page, "04-completion.png");

  const manifest = {
    captions: {
      "01-instructions.png": "Instructions explain the same/different color task and F/J keyboard shortcuts.",
      "02-trial-response-disabled.png": "Response buttons are visible but disabled during the timed fixation/stimulus/blank sequence.",
      "03-trial-response-enabled.png": "Same/Different response prompt is active after the blank interval.",
      "04-completion.png": "Participant reaches the completion page after 10 trials.",
    },
  };
  fs.writeFileSync(
    path.join(screenshotsDir, "manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
  );
});
