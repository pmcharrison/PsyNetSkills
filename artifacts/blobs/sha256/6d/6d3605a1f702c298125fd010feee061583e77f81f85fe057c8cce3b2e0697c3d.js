const { chromium } = require("playwright");

const participantUrl = process.env.PARTICIPANT_URL;
if (!participantUrl) {
  throw new Error("PARTICIPANT_URL is required.");
}

const sequences = [
  ["Low", "Medium", "High"],
  ["High", "Medium", "Low"],
  ["Medium", "Low", "Medium", "High"],
  ["Low", "High", "Medium", "Low"],
];

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function clickButton(page, name) {
  const button = page.getByRole("button", { name: new RegExp(`^${name}$`, "i") }).first();
  await button.waitFor({ state: "visible", timeout: 15000 });
  await button.click({ timeout: 15000 });
}

async function clickEnabledButton(page, name) {
  const button = page.getByRole("button", { name: new RegExp(`^${name}$`, "i") }).first();
  await button.waitFor({ state: "visible", timeout: 15000 });
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (await button.isEnabled()) {
      await button.click();
      return;
    }
    await sleep(200);
  }
  throw new Error(`Button did not become enabled: ${name}`);
}

(async () => {
  const browser = await chromium.launch({
    channel: "chrome",
    headless: false,
    args: [
      "--autoplay-policy=no-user-gesture-required",
      "--window-position=0,0",
      "--window-size=1280,720",
    ],
  });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();

  await page.goto(participantUrl, { waitUntil: "domcontentloaded" });
  try {
    await sleep(1000);
    await clickButton(page, "Begin Experiment");
    await page.getByText(/To proceed, click the button below/i).waitFor({ timeout: 20000 });
    await sleep(800);
    await clickButton(page, "Next");
    await page.getByText(/Welcome! In this experiment/i).waitFor({ timeout: 20000 });
    await sleep(800);
    await clickButton(page, "Next");

    for (let trialIndex = 0; trialIndex < sequences.length; trialIndex += 1) {
      await page.getByText(/Sequence \d+/i).waitFor({ timeout: 20000 });
      const bodyText = await page.locator("body").innerText();
      const match = bodyText.match(/Sequence (\d+)/i);
      if (!match) {
        throw new Error(`Could not identify sequence number from page text: ${bodyText}`);
      }
      const sequence = sequences[Number(match[1]) - 1];
      await sleep(2500);
      for (const label of sequence) {
        await clickEnabledButton(page, label);
        await sleep(550);
      }
      await clickEnabledButton(page, "Next");
      await sleep(900);
    }

    await page.getByText(/Thank you for participating/i).waitFor({ timeout: 20000 });
    await sleep(2500);
    await clickEnabledButton(page, "Next").catch(() => {});
    await sleep(2000);
  } catch (error) {
    console.error(await page.locator("body").innerText().catch(() => ""));
    throw error;
  } finally {
    await browser.close();
  }
})();
