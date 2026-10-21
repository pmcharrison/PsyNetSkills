const { chromium, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const experimentDir = path.resolve(__dirname, '..');
const attemptDir = path.resolve(experimentDir, '..', '..');
const evidenceDir = path.join(attemptDir, 'evidence');
const screenshotDir = path.join(evidenceDir, 'screenshots');
const videoDir = path.join(evidenceDir, 'playwright-video');
const logPath = path.join(evidenceDir, 'participant-flow.log');

fs.mkdirSync(screenshotDir, { recursive: true });
fs.mkdirSync(videoDir, { recursive: true });

const participantUrl = process.env.PARTICIPANT_URL || 'http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair';
function log(message) {
  fs.appendFileSync(logPath, `${new Date().toISOString()} ${message}\n`);
  console.log(message);
}

async function settle(page) {
  await page.waitForLoadState('domcontentloaded').catch(() => {});
  await page.waitForTimeout(250);
}

async function clickFirstEnabledButton(page, description) {
  const button = page.locator('button:visible:not(.response), input[type="submit"]:visible, a.btn:visible').filter({ hasNotText: /^$/ }).first();
  await button.waitFor({ state: 'visible', timeout: 15000 });
  await expect(button).toBeEnabled({ timeout: 30000 });
  log(`Clicking ${description}: ${await button.innerText().catch(() => 'submit')}`);
  await button.click();
  await settle(page);
}

async function clickRating(page, rating) {
  const choice = page.locator('button.push-button.response.submit:visible').filter({ hasText: new RegExp(`^\\s*${rating}(\\s+-.*)?\\s*$`) }).first();
  await choice.waitFor({ state: 'visible', timeout: 30000 });
  await expect(choice).toBeEnabled({ timeout: 45000 });
  await choice.click();
  await settle(page);
}

async function maybeAcceptConsent(page) {
  const checkboxes = await page.locator('input[type="checkbox"]:visible').count();
  for (let i = 0; i < checkboxes; i += 1) {
    await page.locator('input[type="checkbox"]:visible').nth(i).check({ force: true }).catch(() => {});
  }
}

async function hasVisibleText(page, selector, text) {
  return (await page.locator(`${selector}:visible`, { hasText: text }).count()) > 0;
}

(async () => {
  fs.writeFileSync(logPath, '');
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROME || '/usr/bin/google-chrome',
    args: ['--autoplay-policy=no-user-gesture-required', '--use-fake-ui-for-media-stream'],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();
  page.setDefaultTimeout(30000);

  log(`Opening ${participantUrl}`);
  await page.goto(participantUrl, { waitUntil: 'domcontentloaded' });

  let textScreenshotted = false;
  let audioScreenshotted = false;
  let completed = false;
  let textTrials = 0;
  let audioTrials = 0;
  let safety = 0;

  while (!completed && safety < 120) {
    safety += 1;
    await settle(page);
    const url = page.url();

    if (url.includes('/recruiter-exit')) {
      completed = true;
      break;
    }

    if (await hasVisibleText(page, 'h3', 'Text phase: prose-to-lyrics')) {
      textTrials += 1;
      if (!textScreenshotted) {
        await page.screenshot({ path: path.join(screenshotDir, '01_text_trial.png'), fullPage: true });
        textScreenshotted = true;
        log('Captured text trial screenshot.');
      }
      await clickRating(page, 3);
      log(`Completed text trial ${textTrials}.`);
      continue;
    }

    if (await hasVisibleText(page, 'h3', 'Audio phase: speech-to-song')) {
      audioTrials += 1;
      if (!audioScreenshotted) {
        await page.screenshot({ path: path.join(screenshotDir, '02_audio_trial.png'), fullPage: true });
        audioScreenshotted = true;
        log('Captured audio trial screenshot.');
      }
      await clickRating(page, 4);
      log(`Completed audio trial ${audioTrials}.`);
      continue;
    }

    if (await hasVisibleText(page, 'body', 'Thank you for completing the experiment')) {
      await page.screenshot({ path: path.join(screenshotDir, '03_completion.png'), fullPage: true });
      await clickFirstEnabledButton(page, 'completion button');
      if (textTrials === 15 && audioTrials === 15) {
        completed = true;
      }
      continue;
    }

    if (await hasVisibleText(page, 'h2', 'Speech-to-song and prose-to-lyrics judgments')) {
      await page.screenshot({ path: path.join(screenshotDir, '00_instructions.png'), fullPage: true });
    }

    await maybeAcceptConsent(page);
    await clickFirstEnabledButton(page, 'navigation button');
  }

  if (!completed) throw new Error(`Participant flow did not complete after ${safety} steps at ${page.url()}`);
  if (textTrials !== 15) throw new Error(`Expected 15 text trials, saw ${textTrials}`);
  if (audioTrials !== 15) throw new Error(`Expected 15 audio trials, saw ${audioTrials}`);

  log(`Completed participant flow with ${textTrials} text trials and ${audioTrials} audio trials.`);
  await context.close();
  await browser.close();
})();
