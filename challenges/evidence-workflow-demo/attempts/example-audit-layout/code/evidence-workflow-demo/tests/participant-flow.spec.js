import { expect, test } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const experimentRoot = path.resolve(__dirname, '..');
const attemptRoot = path.resolve(__dirname, '../../..');
const screenshotDir = path.join(attemptRoot, 'evidence', 'screenshots');
const stepMs = Number(process.env.PARTICIPANT_FLOW_STEP_MS || 0);
const captureScreenshots = process.env.PARTICIPANT_FLOW_SCREENSHOTS !== '0';

async function pause() {
  if (stepMs > 0) await new Promise((resolve) => setTimeout(resolve, stepMs));
}

async function screenshot(page, name) {
  if (captureScreenshots) {
    await page.screenshot({ path: path.join(screenshotDir, name), fullPage: true });
  }
}

test('participant flow asserts behavior and captures review screenshots', async ({ page }) => {
  await fs.mkdir(screenshotDir, { recursive: true });
  await page.goto(pathToFileURL(path.join(experimentRoot, 'index.html')).href);

  await expect(page.getByRole('heading', { name: 'Melody matching micro-study' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Start task' })).toBeDisabled();
  await screenshot(page, '01-instructions.png');

  await page.getByLabel('I understand this demonstration task.').check();
  await expect(page.getByRole('button', { name: 'Start task' })).toBeEnabled();
  await pause();
  await page.getByRole('button', { name: 'Start task' }).click();

  await expect(page.getByText('Trial 1 of 2')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Rising' })).toBeDisabled();
  await page.getByRole('button', { name: 'Play melody' }).click();
  await expect(page.getByText('Playing...')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Rising' })).toBeDisabled();
  await expect(page.getByText('Choose the contour now.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Rising' })).toBeEnabled();
  await screenshot(page, '02-trial-ready.png');

  await pause();
  await page.getByRole('button', { name: 'Rising' }).click();
  await expect(page.getByText('Correct - the contour matches.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Next' })).toBeEnabled();
  await screenshot(page, '03-feedback.png');

  await pause();
  await page.getByRole('button', { name: 'Next' }).click();
  await expect(page.getByText('Trial 2 of 2')).toBeVisible();
  await page.getByRole('button', { name: 'Play melody' }).click();
  await expect(page.getByText('Choose the contour now.')).toBeVisible();
  await pause();
  await page.getByRole('button', { name: 'Rising' }).click();
  await expect(page.getByText('Not quite - this one was falling.')).toBeVisible();
  await pause();
  await page.getByRole('button', { name: 'Next' }).click();

  await expect(page.getByRole('heading', { name: 'Thank you' })).toBeVisible();
  await expect(page.getByText('Score: 1 / 2')).toBeVisible();
  await expect(page.locator('#saved-data')).toContainText('"trial": 2');
  await expect(page.locator('#saved-data')).toContainText('"correct": false');
  await screenshot(page, '04-completion.png');
  await pause();
});
