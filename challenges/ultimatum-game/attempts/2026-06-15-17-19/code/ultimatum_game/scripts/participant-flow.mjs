import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const AD_URL =
  process.env.PSYNET_AD_URL ||
  "http://localhost:5000/ad?recruiter=hotair&generate_tokens=1&mode=debug";
const CHROME = process.env.CHROME_PATH || "/usr/local/bin/google-chrome";
const EVIDENCE_DIR = path.resolve(
  process.env.EVIDENCE_DIR || "../../evidence/screenshots",
);
const HEADLESS = process.env.HEADLESS !== "0";

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
const captions = {};

async function launchParticipant(name, x) {
  const browser = await chromium.launch({
    headless: HEADLESS,
    executablePath: CHROME,
    args: [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--use-gl=swiftshader",
      "--window-size=640,720",
      `--window-position=${x},0`,
    ],
  });
  const page = await browser.newPage({ viewport: { width: 640, height: 720 } });
  page.setDefaultTimeout(45000);
  page.on("console", (msg) => {
    if (msg.type() === "error") console.log(`[${name}] ${msg.text()}`);
  });
  return { browser, page, name };
}

async function screenshot(participant, filename, caption) {
  await mkdir(EVIDENCE_DIR, { recursive: true });
  await participant.page.screenshot({
    path: path.join(EVIDENCE_DIR, filename),
    fullPage: true,
  });
  captions[filename] = caption;
}

async function writeManifest() {
  await mkdir(EVIDENCE_DIR, { recursive: true });
  await writeFile(
    path.join(EVIDENCE_DIR, "manifest.json"),
    JSON.stringify({ captions }, null, 2) + "\n",
  );
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
  await participant.page.locator("#round-heading", { hasText: roundLabel }).waitFor();
}

async function role(participant) {
  const text = (await participant.page.locator("#role-summary").innerText()).toLowerCase();
  return text.includes("proposer") ? "proposer" : "responder";
}

async function proposerResponder(p1, p2) {
  const r1 = await role(p1);
  return r1 === "proposer"
    ? { proposer: p1, responder: p2 }
    : { proposer: p2, responder: p1 };
}

async function clickOffer(participant, offer) {
  await participant.page.locator("#offer-slider").evaluate((slider, value) => {
    slider.value = value;
    slider.dispatchEvent(new Event("input", { bubbles: true }));
  }, String(offer));
  await participant.page.locator("#offer-button").click();
}

async function clickDecision(participant, decision) {
  const selector = decision === "accept" ? "#accept-button" : "#reject-button";
  await participant.page.locator(selector).click();
}

async function playRound(p1, p2, roundIndex) {
  await Promise.all([
    waitRound(p1, `Scored round ${roundIndex}`),
    waitRound(p2, `Scored round ${roundIndex}`),
  ]);
  const { proposer, responder } = await proposerResponder(p1, p2);
  if (roundIndex === 1) {
    await screenshot(
      proposer,
      "02_proposer_offer_interface.png",
      "Proposer view with the three.js table, avatars, coin split preview, and offer slider.",
    );
  }
  await clickOffer(proposer, offers[roundIndex - 1]);
  await responder.page.locator("#accept-button, #reject-button").first().waitFor({ state: "visible" });
  if (roundIndex === 1) {
    await screenshot(
      responder,
      "03_responder_decision_interface.png",
      "Responder view after the live proposal update, showing accept/reject controls and coin allocation.",
    );
  }
  await clickDecision(responder, decisions[roundIndex - 1]);
  if (roundIndex === 1) {
    await p1.page.locator("#feedback-area", { hasText: "Your cumulative score" }).waitFor();
    await screenshot(
      p1,
      "04_round_feedback_interface.png",
      "Synchronized round feedback in the three.js interface after the responder decision.",
    );
  }
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
    await screenshot(
      p1,
      "01_timeout_demo_interface.png",
      "Timeout demonstration round using the imported three.js tabletop interface.",
    );
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
    await screenshot(
      p1,
      "05_completion_page.png",
      "Completion page after both participants finish the required counted rounds.",
    );
    await writeManifest();
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
