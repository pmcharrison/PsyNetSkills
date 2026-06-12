const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const baseURL = process.env.PSYNET_BASE_URL || 'http://127.0.0.1:5000';
const evidenceDir = path.resolve(__dirname, '../../../evidence');
const screenshotsDir = path.join(evidenceDir, 'screenshots');
const visualMode = process.env.VISUAL_EVIDENCE === '1';

async function saveScreenshot(page, fileName) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  await page.screenshot({ path: path.join(screenshotsDir, fileName), fullPage: true });
}

async function clickAndWait(page, locator) {
  await Promise.all([
    page.waitForLoadState('networkidle').catch(() => {}),
    locator.click(),
  ]);
  if (visualMode) {
    await page.waitForTimeout(500);
  }
}

async function pressAndWait(page, key) {
  await Promise.all([
    page.waitForLoadState('networkidle').catch(() => {}),
    page.keyboard.press(key),
  ]);
  if (visualMode) {
    await page.waitForTimeout(500);
  }
}

test.describe.configure({ mode: 'serial' });

test('participant can complete visual similarity flow', async ({ page }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 1280, height: 720 });

  await page.goto(`${baseURL}/ad?generate_tokens=true&recruiter=hotair`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('button', { name: /Begin Experiment/i })).toBeVisible();
  await saveScreenshot(page, '01-ad-page.png');
  await clickAndWait(page, page.getByRole('button', { name: /Begin Experiment/i }));

  await expect(page.getByRole('button', { name: /^Next$/i })).toBeVisible();
  await saveScreenshot(page, '02-consent-page.png');
  await clickAndWait(page, page.getByRole('button', { name: /^Next$/i }));

  await expect(page.getByText(/pairs of colored circles/i)).toBeVisible();
  await expect(page.getByText(/keys 1 through 5/i)).toBeVisible();
  await saveScreenshot(page, '03-instructions.png');
  await clickAndWait(page, page.getByRole('button', { name: /^Next$/i }));

  const ratings = [
    /1 Completely dissimilar/i,
    /^2$/,
    /^3$/,
    /^4$/,
    /5 Completely similar/i,
  ];

  for (let trial = 1; trial <= 10; trial += 1) {
    await expect(page.getByText(/How similar are these two circles/i)).toBeVisible({ timeout: 10000 });
    for (const rating of ratings) {
      await expect(page.getByRole('button', { name: rating })).toBeVisible();
    }
    await expect.poll(async () => page.locator('svg circle').count(), { timeout: 5000 }).toBeGreaterThanOrEqual(2);
    await expect(page.getByRole('button', { name: /^3$/ })).toBeEnabled();
    if (trial === 1) {
      await saveScreenshot(page, '04-first-trial.png');
    }
    if (trial === 2) {
      await pressAndWait(page, 'Digit3');
    } else {
      await clickAndWait(page, page.getByRole('button', { name: trial % 3 === 0 ? /5 Completely similar/i : /^3$/ }));
    }
    if (visualMode) {
      await page.waitForTimeout(350);
    }
  }

  await expect(page.getByText(/Thank you for your participation/i)).toBeVisible({ timeout: 10000 });
  await saveScreenshot(page, '05-thank-you.png');
  const next = page.getByRole('button', { name: /^Next$/i });
  if (await next.isVisible().catch(() => false)) {
    await clickAndWait(page, next);
  }
  await page.waitForLoadState('networkidle').catch(() => {});
  await saveScreenshot(page, '06-completion.png');
  const finish = page.getByRole('button', { name: /^Finish$/i });
  if (await finish.isVisible().catch(() => false)) {
    await Promise.all([
      page.waitForURL(/recruiter-exit/, { timeout: 15000 }).catch(() => {}),
      finish.click(),
    ]);
  }
  await expect(page).toHaveURL(/recruiter-exit/);
  await saveScreenshot(page, '07-recruiter-exit.png');

  fs.writeFileSync(
    path.join(evidenceDir, 'participant-flow.json'),
    JSON.stringify({ completedTrials: 10, keyboardTrial: 2, finalUrl: page.url() }, null, 2) + '\n',
  );
});
