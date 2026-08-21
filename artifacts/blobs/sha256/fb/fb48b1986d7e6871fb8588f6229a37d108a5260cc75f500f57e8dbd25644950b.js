const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const evidenceDir = path.resolve(__dirname, '../../../evidence');
const screenshotDir = path.join(evidenceDir, 'screenshots');

async function clickVisibleButton(page, label) {
  const button = page.getByRole('button', { name: label }).first();
  await expect(button).toBeVisible({ timeout: 15000 });
  await button.click();
}

async function next(page) {
  await clickVisibleButton(page, /Next|I can hear the clicks|Start/i);
}

test('participant can complete calibration and a main tapping trial', async ({ page }) => {
  fs.mkdirSync(screenshotDir, { recursive: true });
  const url = process.env.PSYNET_PARTICIPANT_URL;
  expect(url, 'PSYNET_PARTICIPANT_URL must be set').toBeTruthy();
  await page.goto(url);
  await page.setViewportSize({ width: 1280, height: 720 });

  await page.screenshot({ path: path.join(screenshotDir, '01-introduction.png'), fullPage: true });
  await next(page);

  await expect(page.getByText(/Play the sample click track/i)).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: path.join(screenshotDir, '02-volume-check.png'), fullPage: true });
  const playButton = page.getByRole('button', { name: /Play volume-check clicks/i }).first();
  if (await playButton.isVisible()) await playButton.click();
  await page.waitForTimeout(900);
  await clickVisibleButton(page, /I can hear the clicks/i);

  await expect(page.getByText(/Calibration/i)).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: path.join(screenshotDir, '03-calibration.png'), fullPage: true });
  await clickVisibleButton(page, /Start/i);
  const tap = page.getByRole('button', { name: /Tap beat/i }).first();
  await expect(tap).toBeVisible({ timeout: 15000 });
  for (const delay of [800, 600, 600, 600, 600]) {
    await page.waitForTimeout(delay);
    await tap.click();
  }
  await clickVisibleButton(page, /Next/i);

  await expect(page.getByText(/main trials will now begin/i)).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: path.join(screenshotDir, '04-calibration-passed.png'), fullPage: true });
  await clickVisibleButton(page, /Next/i);

  await expect(page.getByText(/Main tapping trial/i)).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: path.join(screenshotDir, '05-main-trial.png'), fullPage: true });
  await clickVisibleButton(page, /Start/i);
  for (const delay of [800, 667, 667, 667, 667, 667]) {
    await page.waitForTimeout(delay);
    await tap.click();
  }
  await page.screenshot({ path: path.join(screenshotDir, '06-main-taps-entered.png'), fullPage: true });
});
