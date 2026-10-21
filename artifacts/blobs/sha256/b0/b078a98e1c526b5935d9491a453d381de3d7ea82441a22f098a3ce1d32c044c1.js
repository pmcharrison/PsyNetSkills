const { chromium } = require("@playwright/test");

const participantUrl = process.env.PARTICIPANT_URL;
const evidenceDir = process.env.EVIDENCE_DIR || "../../evidence";
const paceMs = Number.parseInt(process.env.HUMAN_PACE_MS || "450", 10);

if (!participantUrl) {
  throw new Error("PARTICIPANT_URL is required.");
}

const ishiharaAnswers = ["12", "8", "29", "5", "3", "15"];

async function pause(page, multiplier = 1) {
  await page.waitForTimeout(paceMs * multiplier);
}

async function screenshot(page, name) {
  await page.screenshot({ path: `${evidenceDir}/${name}.png`, fullPage: true });
}

async function clickLocator(locator) {
  const count = await locator.count();
  for (let i = 0; i < count; i += 1) {
    const item = locator.nth(i);
    if (await item.isVisible().catch(() => false)) {
      await item.click();
      return true;
    }
  }
  return false;
}

async function clickNextLike(page) {
  const selectors = [
    "button:has-text('Begin Experiment'):visible:not([disabled])",
    "button:has-text('I agree'):visible:not([disabled])",
    "button:has-text('Next'):visible:not([disabled])",
    "button:has-text('Finish'):visible:not([disabled])",
    "input[type='submit']:visible:not([disabled])",
    ".btn:visible:not([disabled])",
  ];
  for (const selector of selectors) {
    if (await clickLocator(page.locator(selector))) {
      return true;
    }
  }
  return false;
}

async function completeFlow() {
  const browser = await chromium.launch({
    channel: "chrome",
    headless: false,
    slowMo: 80,
    args: ["--window-size=1280,720", "--no-sandbox"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto(participantUrl, { waitUntil: "domcontentloaded" });

  let ishiharaIndex = 0;
  let savedDiscrimination = false;
  let savedSimilarity = false;
  let savedIdentification = false;

  for (let step = 0; step < 320; step += 1) {
    await pause(page);
    const text = await page.locator("body").innerText().catch(() => "");

    if (/thank you for completing the experiment|you have finished the experiment/i.test(text)) {
      await screenshot(page, "completion");
      await pause(page, 3);
      break;
    }

    if (/identical or different/i.test(text) && !savedDiscrimination) {
      await screenshot(page, "same_different_trial");
      savedDiscrimination = true;
    }
    if (/rate how similar/i.test(text) && !savedSimilarity) {
      await screenshot(page, "similarity_trial");
      savedSimilarity = true;
    }
    if (/which numbered item was most similar/i.test(text) && !savedIdentification) {
      await screenshot(page, "identification_probe_trial");
      savedIdentification = true;
    }

    const visibleTaskButton = page.locator(".response-choice:visible:not([disabled]), .push-button:visible:not([disabled])");
    if ((await visibleTaskButton.count()) > 0) {
      await pause(page, 2);
      await visibleTaskButton.first().click();
      continue;
    }

    const textInput = page.locator("input[type='text']:visible, textarea:visible").first();
    if ((await textInput.count()) > 0) {
      await pause(page);
      await textInput.fill(ishiharaAnswers[ishiharaIndex] || "test");
      ishiharaIndex += 1;
      await pause(page);
      await clickNextLike(page);
      continue;
    }

    const numberInput = page.locator("input[type='number']:visible").first();
    if ((await numberInput.count()) > 0) {
      await numberInput.fill("30");
      await pause(page);
      await clickNextLike(page);
      continue;
    }

    const select = page.locator("select:visible").first();
    if ((await select.count()) > 0) {
      const values = await select.locator("option").evaluateAll((options) =>
        options.map((option) => option.value).filter((value) => value !== "")
      );
      if (values.length > 0) {
        await select.selectOption(values[0]);
      }
      await pause(page);
      await clickNextLike(page);
      continue;
    }

    const radio = page.locator("input[type='radio']:visible").first();
    if ((await radio.count()) > 0) {
      await radio.check();
      await pause(page);
      await clickNextLike(page);
      continue;
    }

    await clickNextLike(page);
  }

  await browser.close();
}

completeFlow();
