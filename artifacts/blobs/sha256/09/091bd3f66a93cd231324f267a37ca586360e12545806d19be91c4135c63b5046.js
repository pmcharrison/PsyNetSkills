/*
 * Drives one participant through the cross_cultural_choice experiment with
 * human-like pacing, for participant video evidence.
 *
 * Usage: node run.js <ad_url>
 *
 * Launches headed Chrome (channel "chrome") on the current DISPLAY so the
 * session can be captured with ffmpeg x11grab.
 */

const { chromium } = require("@playwright/test");

const AD_URL = process.argv[2] || "http://localhost:5000/ad?recruiter=generic&generic_mode=debug";

const PAUSE_SHORT = 1200; // after page settles
const PAUSE_READ = 2600; // "reading" a page before acting

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const browser = await chromium.launch({
    headless: false,
    channel: "chrome",
    args: ["--window-size=1280,720", "--window-position=0,0", "--no-first-run"],
  });
  const context = await browser.newContext({ viewport: { width: 1280, height: 690 } });
  const page = await context.newPage();

  console.log(`Opening ad page: ${AD_URL}`);
  await page.goto(AD_URL, { waitUntil: "networkidle" });
  await sleep(PAUSE_READ);

  const begin = page.locator("#begin-button");
  if (await begin.count()) {
    console.log("Clicking begin button");
    await begin.click();
    await page.waitForLoadState("networkidle");
    await sleep(PAUSE_SHORT);
  }

  const consent = page.locator("#consent");
  if (await consent.count()) {
    console.log("Clicking consent button");
    await consent.click();
  }

  // Walk through the timeline: welcome, instructions, 6 choice trials,
  // thank-you, final page.
  for (let step = 0; step < 30; step++) {
    await page.waitForLoadState("domcontentloaded");
    await sleep(PAUSE_READ);

    // The recruiter exit page URL is locale-independent, unlike the page text.
    const finished = page.url().includes("recruiter-exit");
    if (finished) {
      console.log("Reached final page");
      await sleep(PAUSE_SHORT);
      break;
    }

    // Choice trials have two push buttons; the end page has a single
    // "Finish" push button.
    const optionButtons = page.locator("button.push-button");
    const nOptions = await optionButtons.count();
    if (nOptions >= 1) {
      const pick = Math.floor(Math.random() * nOptions);
      const label = await optionButtons.nth(pick).innerText();
      console.log(`Push-button page: clicking button ${pick + 1}/${nOptions} (“${label.trim()}”)`);
      await sleep(PAUSE_SHORT); // extra time "comparing" the two options
      await optionButtons.nth(pick).click();
      continue;
    }

    const nextButton = page.locator("#next-button");
    if ((await nextButton.count()) && (await nextButton.isEnabled().catch(() => false))) {
      console.log("Info page: clicking next");
      await nextButton.click();
      continue;
    }

    const bodySnippet = await page
      .locator("body")
      .innerText()
      .then((t) => t.replace(/\n+/g, " | ").slice(0, 150))
      .catch(() => "<unavailable>");
    console.log(`No actionable element found; waiting (url=${page.url()}, body=${bodySnippet})`);
    await sleep(PAUSE_SHORT);
  }

  await sleep(2000);
  await browser.close();
  console.log("DONE");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
