const { chromium } = require("playwright");

const BASE_URL = process.env.PSYNET_BASE_URL || "http://127.0.0.1:5000";
const PARTICIPANT_URL = `${BASE_URL}/ad?generate_tokens=true&recruiter=hotair`;
const TIMEOUT_MS = 90000;

async function wait(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function text(page) {
  return ((await page.locator("body").innerText().catch(() => "")) || "").trim();
}

async function clickIfVisible(page, selector) {
  const locator = page.locator(selector).first();
  if ((await locator.count()) > 0 && (await locator.isVisible().catch(() => false))) {
    await locator.click({ timeout: 5000 }).catch(() => {});
    return true;
  }
  return false;
}

async function clickNextIfReady(page) {
  const button = page.locator("#next-button").first();
  if ((await button.count()) === 0) return false;
  if (!(await button.isVisible().catch(() => false))) return false;
  if (!(await button.isEnabled().catch(() => false))) return false;
  await button.click();
  return true;
}

async function waitForContribution(page, participantLabel) {
  const deadline = Date.now() + TIMEOUT_MS;
  while (Date.now() < deadline) {
    const body = await text(page);
    if (body.includes("experiment must end early")) {
      throw new Error(`${participantLabel} ended early: ${body}`);
    }
    if ((await page.locator("#number-input").count()) > 0) {
      return;
    }
    await clickIfVisible(page, "#consent");
    await clickIfVisible(page, "#begin-button, button.btn-primary");
    await clickNextIfReady(page);
    await wait(250);
  }
  throw new Error(`${participantLabel} did not reach a contribution page.`);
}

async function waitForFeedback(page, roundNumber, participantLabel) {
  const expected = `Round ${roundNumber} feedback`;
  await page.waitForFunction(
    (needle) => document.body && document.body.innerText.includes(needle),
    expected,
    { timeout: TIMEOUT_MS }
  );
  const body = await text(page);
  if (!body.includes("Total group contribution") || !body.includes("After the 10% increase")) {
    throw new Error(`${participantLabel} feedback is missing common-pool math.`);
  }
  return body;
}

async function submitContribution(page, amount) {
  await page.locator("#number-input").fill(String(amount));
  await clickNextIfReady(page);
}

async function advancePastFeedback(page) {
  const deadline = Date.now() + TIMEOUT_MS;
  while (Date.now() < deadline) {
    if ((await page.locator("#number-input").count()) > 0) return;
    const body = await text(page);
    if (body.includes("Task complete")) return;
    await clickNextIfReady(page);
    await wait(250);
  }
  throw new Error("Timed out advancing past feedback.");
}

async function main() {
  const browser = await chromium.launch({
    headless: false,
    executablePath: "/usr/local/bin/google-chrome",
    args: ["--window-size=1280,720", "--window-position=0,0", "--no-sandbox"],
  });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const pages = await Promise.all([context.newPage(), context.newPage(), context.newPage()]);

  for (let i = 0; i < pages.length; i += 1) {
    await pages[i].goto(PARTICIPANT_URL);
    await pages[i].bringToFront();
    await wait(300);
  }

  await Promise.all(pages.map((page, i) => waitForContribution(page, `P${i + 1}`)));
  console.log("All three participants reached round 1 contribution pages.");

  await pages[0].bringToFront();
  console.log("P1 is being left idle to demonstrate timeout-to-maximum contribution.");
  await submitContribution(pages[1], 10);
  await submitContribution(pages[2], 20);
  await pages[0].bringToFront();

  const roundOneFeedback = await Promise.all(
    pages.map((page, i) => waitForFeedback(page, 1, `P${i + 1}`))
  );
  console.log("Round 1 feedback observed after P1 timeout.");
  console.log(roundOneFeedback[0].split("\n").filter(Boolean).slice(0, 12).join(" | "));
  await pages[0].bringToFront();
  await wait(6000);

  for (let round = 2; round <= 10; round += 1) {
    await Promise.all(pages.map(advancePastFeedback));
    await Promise.all(pages.map((page, i) => submitContribution(page, 5 + i + round)));
    await Promise.all(pages.map((page, i) => waitForFeedback(page, round, `P${i + 1}`)));
    console.log(`Round ${round} feedback observed for all participants.`);
    await pages[0].bringToFront();
    await wait(round === 10 ? 3000 : 750);
  }

  await Promise.all(pages.map(advancePastFeedback));
  await pages[0].bringToFront();
  await pages[0].waitForFunction(
    () => document.body && document.body.innerText.includes("Task complete"),
    { timeout: TIMEOUT_MS }
  );
  console.log((await text(pages[0])).split("\n").filter(Boolean).slice(0, 8).join(" | "));
  await wait(5000);
  await browser.close();
}

main().catch(async (error) => {
  console.error(error);
  process.exit(1);
});
