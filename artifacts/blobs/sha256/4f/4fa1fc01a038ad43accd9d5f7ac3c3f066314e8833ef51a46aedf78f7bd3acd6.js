const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.PSYNET_BASE_URL || 'http://127.0.0.1:5000';
const PARTICIPANT_URL = `${BASE_URL}/ad?generate_tokens=true&recruiter=hotair`;
const evidenceDir = path.resolve(__dirname, '../../../evidence');
const screenshotDir = path.join(evidenceDir, 'screenshots');
const videoDir = path.join(evidenceDir, 'playwright-video');

async function clickFirstEnabledButton(page) {
  const selectors = [
    'button:visible:not([disabled])',
    'input[type="submit"]:visible:not([disabled])',
    '.push-button:visible:not([disabled])',
    '.btn:visible:not([disabled])',
  ];
  for (const selector of selectors) {
    const locator = page.locator(selector);
    const count = await locator.count();
    for (let i = 0; i < count; i += 1) {
      const item = locator.nth(i);
      if (await item.isVisible().catch(() => false)) {
        await Promise.all([
          page.waitForLoadState('domcontentloaded', { timeout: 5000 }).catch(() => {}),
          item.click(),
        ]);
        return true;
      }
    }
  }
  return false;
}

async function reachDiscoveryInstruction(page) {
  await page.goto(PARTICIPANT_URL, { waitUntil: 'domcontentloaded' });
  for (let i = 0; i < 30; i += 1) {
    if (await page.locator('#instruction-next').isVisible().catch(() => false)) return;
    await clickFirstEnabledButton(page);
    await page.waitForTimeout(800);
  }
  await expect(page.locator('#instruction-next')).toBeVisible({ timeout: 10000 });
}

async function performScriptedGame(page) {
  await page.locator('#game-grid').click();
  const keys = ['Space', 'ArrowRight', 'Space', 'ArrowLeft', 'Space', 'ArrowDown', 'Space', 'ArrowUp', 'd', 'Space', 'ArrowDown', 'ArrowRight', 'Space', 'ArrowLeft', 'Space'];
  for (const key of keys) {
    await page.keyboard.press(key);
    await page.waitForTimeout(90);
  }
  await expect(page.locator('#points')).toHaveText('20');
  await page.locator('#finish-review').click();
}

async function completeSeedParticipant(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  await reachDiscoveryInstruction(page);
  await page.locator('#instruction-next').click();
  await expect(page.locator('#game-grid')).toBeVisible({ timeout: 10000 });
  await performScriptedGame(page);
  await expect(page.locator('#submit-answer')).toBeVisible();
  await page.locator('#message-how').fill('Seed participant found same-shape fusions and harvested the upgraded crystals.');
  await page.locator('#message-rules').fill('Same-shape crystals fused in this easy condition. Harvest after each successful fusion.');
  await page.locator('#submit-answer').click();
  await page.waitForTimeout(1000);
  await context.close();
}

test('participant sees aggregated messages and plays discovery game', async ({ browser }) => {
  test.setTimeout(120000);
  fs.mkdirSync(screenshotDir, { recursive: true });
  fs.mkdirSync(videoDir, { recursive: true });

  await completeSeedParticipant(browser);
  await completeSeedParticipant(browser);
  await new Promise((resolve) => setTimeout(resolve, 1500));

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();
  await reachDiscoveryInstruction(page);
  await page.screenshot({ path: path.join(screenshotDir, '01-instructions.png'), fullPage: true });

  await page.locator('#instruction-next').click();
  await expect(page.locator('text=messages from previous players')).toBeVisible({ timeout: 10000 });
  await expect(page.locator('.message-card')).toHaveCount(2);
  await page.screenshot({ path: path.join(screenshotDir, '02-aggregated-messages.png'), fullPage: true });

  await page.locator('.open-message').first().click();
  await page.evaluate(() => {
    const el = document.querySelector('.message-text');
    const range = document.createRange();
    range.selectNodeContents(el);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  });
  await page.locator('.save-note').first().click();
  await expect(page.locator('#messages-next')).toBeEnabled();
  await page.screenshot({ path: path.join(screenshotDir, '03-notebook-note.png'), fullPage: true });

  await page.locator('#messages-next').click();
  await page.locator('#strategy-summary').fill('Fuse same-shape crystals, then harvest upgraded crystals.');
  await expect(page.locator('#start-game')).toBeEnabled();
  await page.locator('#start-game').click();
  await expect(page.locator('#game-grid')).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: path.join(screenshotDir, '04-game-grid.png'), fullPage: true });

  await performScriptedGame(page);
  await expect(page.locator('#submit-answer')).toBeVisible();
  await page.screenshot({ path: path.join(screenshotDir, '05-outgoing-messages.png'), fullPage: true });
  await page.locator('#message-how').fill('I used the previous messages and fused same-shape crystals for points.');
  await page.locator('#message-rules').fill('Same-shape crystals fuse in the easy condition; harvest the upgraded crystal.');
  await page.locator('#submit-answer').click();
  await page.waitForTimeout(1000);

  const video = await page.video().path();
  await context.close();
  fs.copyFileSync(video, path.join(evidenceDir, 'participant.webm'));

  const manifest = {
    captions: {
      'screenshots/01-instructions.png': 'Generation 1 participant instructions before reading aggregated messages.',
      'screenshots/02-aggregated-messages.png': 'Generation 1 receives two ranked messages aggregated from generation 0.',
      'screenshots/03-notebook-note.png': 'Participant marks a message read and saves highlighted text to the notebook.',
      'screenshots/04-game-grid.png': 'Crystal grid with rover, points, actions remaining, carrying/current-tile status, hints, and logs.',
      'screenshots/05-outgoing-messages.png': 'Outgoing strategy and rule message composition after game play.',
    }
  };
  fs.writeFileSync(path.join(screenshotDir, 'manifest.json'), JSON.stringify(manifest, null, 2));
});
