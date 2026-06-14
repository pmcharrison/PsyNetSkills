// Participant-flow evidence runner for the simple visual similarity experiment.
//
// Drives one participant through the whole flow (ad -> consent -> instructions ->
// 10 similarity-rating trials -> completion), capturing targeted screenshots and
// asserting key participant-facing behavior. Reaction-time responses are entered
// with the keyboard (digit keys 1-5), exercising the KeyboardPushButtonControl.
//
// Run with the experiment server already up (`psynet debug local`):
//   PARTICIPANT_URL="http://127.0.0.1:5000/ad?recruiter=hotair&generate_tokens=true" \
//     npx playwright test

const { test, expect } = require("@playwright/test");
const path = require("path");

const SHOTS = path.resolve(__dirname, "../../../evidence/screenshots");
const PARTICIPANT_URL =
  process.env.PARTICIPANT_URL ||
  "http://127.0.0.1:5000/ad?recruiter=hotair&generate_tokens=true";
const N_TRIALS = 10;
// Ratings entered across the 10 trials (1=dissimilar ... 5=similar).
const RATINGS = [5, 1, 3, 4, 2, 5, 2, 4, 1, 3];

test("participant completes the visual similarity experiment", async ({ page }) => {
  test.setTimeout(170000);

  // 1. Ad page.
  await page.goto(PARTICIPANT_URL);
  const begin = page.locator("#begin-button");
  await expect(begin).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/01-ad-page.png` });
  await page.waitForTimeout(800);
  await begin.click();

  // 2. Consent page.
  const consent = page.locator("#consent");
  await expect(consent).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/02-consent.png` });
  await page.waitForTimeout(800);
  await consent.click();

  // 3. Instructions page.
  const next = page.locator("#next-button");
  await expect(next).toBeVisible();
  await expect(page.locator("body")).toContainText("similar");
  await page.screenshot({ path: `${SHOTS}/03-instructions.png`, fullPage: true });
  await page.waitForTimeout(1200);
  await next.click();

  // 4. Trials.
  for (let i = 0; i < N_TRIALS; i++) {
    // The trial page renders the 5 rating buttons (initially disabled while the
    // fixation cross is shown).
    const buttons = page.locator(".push-button");
    await expect(buttons).toHaveCount(5, { timeout: 20000 });

    if (i === 0) {
      // Let Raphael draw the fixation cross (still within the 0.8s fixation
      // frame, before the buttons enable), then capture it.
      await page.waitForTimeout(300);
      await page.screenshot({ path: `${SHOTS}/04-fixation.png` });
    }

    // Buttons are enabled once the stimulus pair appears (responseEnable fires at
    // the stimulus frame).
    const enabledButton = page.locator(".push-button:not([disabled])").first();
    await expect(enabledButton).toBeVisible({ timeout: 20000 });

    if (i === 0) {
      await page.screenshot({ path: `${SHOTS}/05-stimulus-pair.png` });
    }

    // Brief pause so the recording shows the stimulus before the response.
    await page.waitForTimeout(700);

    // Respond using the keyboard (demonstrates keyboard input + reaction time).
    const rating = RATINGS[i % RATINGS.length];
    await page.keyboard.press(`Digit${rating}`);
    await page.waitForTimeout(400);
  }

  // 5. Custom "Thank you" info page.
  const finalNext = page.locator("#next-button");
  await expect(finalNext).toBeVisible({ timeout: 20000 });
  await page.screenshot({ path: `${SHOTS}/06-thank-you.png` });
  await page.waitForTimeout(800);
  await finalNext.click();

  // 6. PsyNet end page presents its "Finish" button as a single .push-button.
  const finish = page.locator(".push-button");
  await expect(finish).toHaveCount(1, { timeout: 20000 });
  await page.waitForTimeout(600);
  await finish.click();

  // 7. Completion is detected via the locale-independent recruiter-exit URL.
  await page.waitForURL(/recruiter-exit/, { timeout: 20000 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${SHOTS}/07-completion.png` });
  expect(page.url()).toMatch(/recruiter-exit/);
});
