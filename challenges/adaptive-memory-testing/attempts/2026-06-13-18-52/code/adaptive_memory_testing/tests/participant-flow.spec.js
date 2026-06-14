const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const participantUrl = process.env.PARTICIPANT_URL;
const evidenceDir = path.resolve(__dirname, '../../../evidence');
const screenshotDir = path.join(evidenceDir, 'screenshots');

function ensureEvidenceDirs() {
  fs.mkdirSync(screenshotDir, { recursive: true });
}

async function clickNextIfVisible(page) {
  const buttons = page.locator('button.push-button, button, input[type="submit"]');
  const count = await buttons.count();
  for (let i = 0; i < count; i++) {
    const button = buttons.nth(i);
    if (await button.isVisible()) {
      if (await button.isDisabled().catch(() => false)) continue;
      const text = (await button.innerText().catch(() => '')).trim();
      const value = (await button.getAttribute('value').catch(() => '') || '').trim();
      if (/begin|next|finish|start|continue/i.test(`${text} ${value}`)) {
        await button.click();
        return true;
      }
    }
  }
  return false;
}

async function advanceUntilVisible(page, selector, maxClicks = 8) {
  for (let i = 0; i < maxClicks; i++) {
    if (await page.locator(selector).first().isVisible().catch(() => false)) {
      return;
    }
    const clicked = await clickNextIfVisible(page);
    if (!clicked) {
      await page.waitForTimeout(500);
    }
  }
  await page.waitForSelector(selector, { timeout: 60000 });
}

async function waitAndClickNext(page, timeoutMs = 5000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await clickNextIfVisible(page)) return true;
    await page.waitForTimeout(100);
  }
  return false;
}

test('participant completes adaptive memory flow', async ({ page }) => {
  test.setTimeout(180000);
  ensureEvidenceDirs();
  if (!participantUrl) throw new Error('Set PARTICIPANT_URL.');

  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(participantUrl, { waitUntil: 'domcontentloaded' });
  await page.screenshot({ path: path.join(screenshotDir, '01-instructions.png'), fullPage: true });
  await advanceUntilVisible(page, '.digit-string');

  let capturedTrial = false;
  for (let trial = 1; trial <= 10; trial++) {
    await page.waitForSelector('.digit-string', { timeout: 60000 });
    const target = (await page.locator('.digit-string').first().innerText()).trim();
    expect(target).toMatch(/^\d{2,20}$/);
    if (!capturedTrial) {
      await page.screenshot({ path: path.join(screenshotDir, '02-digit-display.png'), fullPage: true });
    }

    await page.waitForSelector('input[type="text"], textarea', { timeout: 60000 });
    const input = page.locator('input[type="text"], textarea').first();
    await expect(input).toBeVisible();
    await expect(input).toBeEnabled({ timeout: 60000 });
    await input.fill(target);
    await page.waitForTimeout(150);
    if (!capturedTrial) {
      await page.screenshot({ path: path.join(screenshotDir, '03-recall-input.png'), fullPage: true });
      capturedTrial = true;
    }
    const clicked = await clickNextIfVisible(page);
    expect(clicked).toBeTruthy();
  }

  await expect.poll(async () => page.url(), { timeout: 60000 }).toMatch(/recruiter-exit|timeline|dashboard|ad/);
  if (!/recruiter-exit/.test(page.url())) {
    await clickNextIfVisible(page);
  }
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(screenshotDir, '04-completion.png'), fullPage: true });

  const manifest = {
    captions: {
      'evidence/screenshots/01-instructions.png': 'Participant instructions describe the 10-trial exact digit recall task.',
      'evidence/screenshots/02-digit-display.png': 'A generated digit string is displayed briefly before recall.',
      'evidence/screenshots/03-recall-input.png': 'The target string is hidden and the participant enters a memory response.',
      'evidence/screenshots/04-completion.png': 'The participant flow reaches completion / recruiter exit.'
    }
  };
  fs.writeFileSync(path.join(screenshotDir, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
});
