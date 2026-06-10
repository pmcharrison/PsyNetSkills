const { chromium } = require("@playwright/test");

const participantUrl = process.env.PARTICIPANT_URL;
if (!participantUrl) {
  throw new Error("PARTICIPANT_URL is required.");
}

const ishiharaAnswers = ["12", "8", "29", "5", "3", "15"];

async function clickFirstVisible(locator, timeout = 15000) {
  const count = await locator.count();
  for (let i = 0; i < count; i += 1) {
    const item = locator.nth(i);
    if (await item.isVisible()) {
      await item.click({ timeout });
      return true;
    }
  }
  return false;
}

async function completeFlow() {
  const browser = await chromium.launch({
    channel: "chrome",
    headless: false,
    args: ["--window-size=1280,720", "--no-sandbox"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto(participantUrl, { waitUntil: "domcontentloaded" });

  let ishiharaIndex = 0;
  for (let step = 0; step < 140; step += 1) {
    await page.waitForTimeout(300);
    const bodyText = await page.locator("body").innerText().catch(() => "");
    if (/thank you for completing the experiment/i.test(bodyText)) {
      await page.waitForTimeout(1500);
      break;
    }

    const visiblePushButton = page.locator(".push-button:visible:not([disabled])");
    if ((await visiblePushButton.count()) > 0) {
      await visiblePushButton.first().click();
      continue;
    }

    const textInput = page.locator("input[type='text']:visible, textarea:visible").first();
    if ((await textInput.count()) > 0) {
      const answer = ishiharaAnswers[ishiharaIndex] || "test";
      ishiharaIndex += 1;
      await textInput.fill(answer);
      await clickFirstVisible(page.locator("button:has-text('Next'):visible:not([disabled])"));
      continue;
    }

    const numberInput = page.locator("input[type='number']:visible").first();
    if ((await numberInput.count()) > 0) {
      await numberInput.fill("30");
      await clickFirstVisible(page.locator("button:has-text('Next'):visible:not([disabled])"));
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
      await clickFirstVisible(page.locator("button:has-text('Next'):visible:not([disabled])"));
      continue;
    }

    const radio = page.locator("input[type='radio']:visible").first();
    if ((await radio.count()) > 0) {
      await radio.check();
      await clickFirstVisible(page.locator("button:has-text('Next'):visible:not([disabled])"));
      continue;
    }

    const nextClicked = await clickFirstVisible(
      page.locator("button:has-text('Next'):visible:not([disabled])"),
      3000
    );
    if (!nextClicked) {
      await page.waitForTimeout(1000);
    }
  }

  await page.screenshot({ path: "../../evidence/participant_final.png", fullPage: true });
  await browser.close();
}

completeFlow();
