import { chromium } from "@playwright/test";

const AD_URL =
  process.env.PSYNET_AD_URL ||
  "http://localhost:5000/ad?recruiter=hotair&generate_tokens=1&mode=debug";
const CHROME = process.env.CHROME_PATH || "/usr/local/bin/google-chrome";

const offers = [5, 2, 7, 4, 6, 3, 5, 8, 1, 5];
const decisions = [
  "accept",
  "reject",
  "accept",
  "accept",
  "accept",
  "accept",
  "accept",
  "accept",
  "reject",
  "accept",
];

async function launchParticipant(name, x) {
  const browser = await chromium.launch({
    headless: false,
    executablePath: CHROME,
    args: [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--window-size=640,720",
      `--window-position=${x},0`,
    ],
  });
  const page = await browser.newPage({ viewport: { width: 640, height: 720 } });
  page.setDefaultTimeout(30000);
  page.on("console", (msg) => {
    if (msg.type() === "error") console.log(`[${name}] ${msg.text()}`);
  });
  return { browser, page, name };
}

async function clickIfVisible(page, selector) {
  const locator = page.locator(selector).first();
  if ((await locator.count()) > 0 && (await locator.isVisible())) {
    await locator.click();
    return true;
  }
  return false;
}

async function reachInstructions(participant) {
  const { page } = participant;
  await page.goto(AD_URL);
  for (let i = 0; i < 20; i++) {
    if (await page.getByText("Repeated Ultimatum Game").isVisible().catch(() => false)) {
      return;
    }
    const clicked =
      (await clickIfVisible(page, "text=Begin Experiment")) ||
      (await clickIfVisible(page, "text=Begin experiment")) ||
      (await clickIfVisible(page, "text=I agree")) ||
      (await clickIfVisible(page, "button:has-text('Next')")) ||
      (await clickIfVisible(page, "button:has-text('Begin')"));
    if (!clicked) await page.waitForTimeout(500);
  }
  throw new Error(`${participant.name} did not reach instructions`);
}

async function clickTimedButton(participant, label) {
  await participant.page.locator(`button:has-text('${label}')`).first().click();
}

async function waitRound(participant, roundLabel) {
  await participant.page.getByRole("heading", { name: roundLabel }).waitFor();
}

async function role(participant) {
  const text = await participant.page.locator("#role-summary").innerText();
  return text.includes("proposer") ? "proposer" : "responder";
}

async function proposerResponder(p1, p2) {
  const r1 = await role(p1);
  return r1 === "proposer"
    ? { proposer: p1, responder: p2 }
    : { proposer: p2, responder: p1 };
}

async function clickOffer(participant, offer) {
  await participant.page
    .locator("#offer-buttons button")
    .filter({ hasText: new RegExp(`^${offer}$`) })
    .click();
}

async function playRound(p1, p2, roundIndex) {
  await Promise.all([
    waitRound(p1, `Scored round ${roundIndex}`),
    waitRound(p2, `Scored round ${roundIndex}`),
  ]);
  const { proposer, responder } = await proposerResponder(p1, p2);
  await clickOffer(proposer, offers[roundIndex - 1]);
  await responder.page.locator("#decision-controls").waitFor({ state: "visible" });
  await responder.page
    .locator(`#${decisions[roundIndex - 1]}-button`)
    .click();
  await Promise.all([
    p1.page.getByText(`Round feedback: ${roundIndex}`).waitFor(),
    p2.page.getByText(`Round feedback: ${roundIndex}`).waitFor(),
  ]);
  await p1.page.waitForTimeout(600);
  await Promise.all([clickTimedButton(p1, "Continue"), clickTimedButton(p2, "Continue")]);
}

async function main() {
  const p1 = await launchParticipant("participant-1", 0);
  const p2 = await launchParticipant("participant-2", 640);
  try {
    await Promise.all([reachInstructions(p1), reachInstructions(p2)]);
    await Promise.all([clickTimedButton(p1, "Begin"), clickTimedButton(p2, "Begin")]);

    await Promise.all([
      waitRound(p1, "Timeout demonstration round"),
      waitRound(p2, "Timeout demonstration round"),
    ]);
    await p1.page.waitForTimeout(9500);
    await Promise.all([
      p1.page.getByText("Round feedback: Timeout demo").waitFor(),
      p2.page.getByText("Round feedback: Timeout demo").waitFor(),
    ]);
    await p1.page.waitForTimeout(600);
    await Promise.all([clickTimedButton(p1, "Continue"), clickTimedButton(p2, "Continue")]);

    for (let round = 1; round <= 10; round++) {
      await playRound(p1, p2, round);
    }

    await Promise.all([
      p1.page.getByText("Task complete").waitFor(),
      p2.page.getByText("Task complete").waitFor(),
    ]);
    await p1.page.waitForTimeout(1500);
  } finally {
    await p1.browser.close();
    await p2.browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
