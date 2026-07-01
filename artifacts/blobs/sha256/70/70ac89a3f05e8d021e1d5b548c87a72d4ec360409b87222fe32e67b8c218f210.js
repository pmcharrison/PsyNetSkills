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

async function clickIfVisible(page, label, timeout = 5000) {
  const button = page.getByRole('button', { name: label }).first();
  try {
    await expect(button).toBeVisible({ timeout });
    await button.click();
    return true;
  } catch {
    return false;
  }
}

async function next(page) {
  await clickVisibleButton(page, /Next|I can hear the clicks|Start/i);
}

async function tapCurrentTrial(page, delays) {
  await clickVisibleButton(page, /Start/i);
  const tap = page.getByRole('button', { name: /Tap beat/i }).first();
  await expect(tap).toBeVisible({ timeout: 15000 });
  for (const delay of delays) {
    await page.waitForTimeout(delay);
    await tap.click();
  }
}

test('participant can complete calibration and a main tapping trial', async ({ page }) => {
  fs.mkdirSync(screenshotDir, { recursive: true });
  const url = process.env.PSYNET_PARTICIPANT_URL;
  expect(url, 'PSYNET_PARTICIPANT_URL must be set').toBeTruthy();
  await page.goto(url);
  await page.setViewportSize({ width: 1280, height: 720 });

  await clickIfVisible(page, /Begin Experiment/i);
  await clickIfVisible(page, /Next/i);
  await expect(page.getByText(/Tap along to generated metronome clicks/i)).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: path.join(screenshotDir, '01-introduction.png'), fullPage: true });
  await next(page);

  await expect(page.getByText(/Play the sample click track/i)).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: path.join(screenshotDir, '02-volume-check.png'), fullPage: true });
  const playButton = page.getByRole('button', { name: /Play volume-check clicks/i }).first();
  if (await playButton.isVisible()) await playButton.click();
  await page.waitForTimeout(900);
  await clickVisibleButton(page, /I can hear the clicks/i);

  await expect(page.getByRole('heading', { name: /Calibration/i })).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: path.join(screenshotDir, '03-calibration.png'), fullPage: true });
  await tapCurrentTrial(page, [800, 600, 600, 600, 600]);
  await clickVisibleButton(page, /Next/i);

  await expect(page.getByText(/main trials will now begin/i)).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: path.join(screenshotDir, '04-calibration-passed.png'), fullPage: true });
  await clickVisibleButton(page, /Next/i);

  for (let trialIndex = 0; trialIndex < 3; trialIndex++) {
    await expect(page.getByText(/Main tapping trial/i).first()).toBeVisible({ timeout: 15000 });
    if (trialIndex === 0) {
      await page.screenshot({ path: path.join(screenshotDir, '05-main-trial.png'), fullPage: true });
    }
    await tapCurrentTrial(page, [800, 667, 667, 667, 667, 667]);
    if (trialIndex === 0) {
      await page.screenshot({ path: path.join(screenshotDir, '06-main-taps-entered.png'), fullPage: true });
    }
    await clickVisibleButton(page, /Next/i);
  }
  await clickIfVisible(page, /Finish|Next/i, 10000);
  await page.waitForURL(/recruiter-exit/, { timeout: 30000 });
  await page.screenshot({ path: path.join(screenshotDir, '07-completion.png'), fullPage: true });
});
