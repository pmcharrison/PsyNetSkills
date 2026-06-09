const { chromium } = require("@playwright/test");

const BASE_URL = process.env.PSYNET_BASE_URL || "http://localhost:5000";
const EVIDENCE_DIR = process.env.EVIDENCE_DIR || "../../evidence";
const ROUNDS = 64;

function participantUrl(workerId) {
  const params = new URLSearchParams({
    recruiter: "hotair",
    assignmentId: `assignment-${workerId}`,
    hitId: "grid-game-demo",
    workerId,
    mode: "debug",
  });
  return `${BASE_URL}/ad?${params.toString()}`;
}

async function clickFirstVisible(page, selectors) {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    if (
      await locator.isVisible().catch(() => false)
      && await locator.isEnabled().catch(() => false)
    ) {
      await locator.click();
      return true;
    }
  }
  return false;
}

async function advanceToGame(page, label) {
  const deadline = Date.now() + 90_000;
  while (Date.now() < deadline) {
    if (
      await page.locator("#own-grid").isVisible().catch(() => false)
      || await page.locator("#finish-btn").isVisible().catch(() => false)
    ) {
      return;
    }
    await clickFirstVisible(page, [
      "button:has-text('I consent')",
      "button:has-text('Begin')",
      "button:has-text('Start')",
      "button:has-text('Next')",
      "button:has-text('Continue')",
      "input[type='submit']",
      ".btn-primary",
    ]);
    await page.waitForTimeout(350);
  }
  throw new Error(`${label} did not reach the grid game`);
}

async function waitForEnabledCell(page) {
  await page.waitForFunction(() => {
    const button = document.querySelector("#own-grid button:not(:disabled)");
    return Boolean(button);
  }, { timeout: 30_000 });
}

async function clickCell(page, row, col) {
  await waitForEnabledCell(page);
  await page.locator(`#own-grid [data-row='${row}'][data-col='${col}']`).click();
}

async function waitForNextRoundOrCompletion(page) {
  await page.waitForFunction(() => {
    return Boolean(
      document.querySelector("#finish-btn:not(:disabled)")
      || document.querySelector("#own-grid button:not(:disabled)")
    );
  }, { timeout: 30_000 });
}

async function ownClickCount(page) {
  return page.locator("#own-grid .own-clicked").count();
}

async function run() {
  const runId = String(Date.now());
  const launchOptions = (x) => ({
    executablePath: process.env.CHROME_PATH || "/usr/local/bin/google-chrome",
    headless: false,
    args: ["--no-sandbox", "--window-size=640,700", `--window-position=${x},0`],
  });
  const browser1 = await chromium.launch(launchOptions(0));
  const browser2 = await chromium.launch(launchOptions(640));
  const context1 = await browser1.newContext({ viewport: { width: 640, height: 700 } });
  const context2 = await browser2.newContext({ viewport: { width: 640, height: 700 } });
  const player1 = await context1.newPage();
  const player2 = await context2.newPage();

  await player1.goto(participantUrl(`grid-player-1-${runId}`));
  await player2.goto(participantUrl(`grid-player-2-${runId}`));
  await Promise.all([
    advanceToGame(player1, "player 1"),
    advanceToGame(player2, "player 2"),
  ]);

  for (let round = 0; round < ROUNDS; round += 1) {
    await Promise.all([
      clickCell(player1, round % 8, (round * 3) % 8),
      clickCell(player2, (round * 5) % 8, (round * 7) % 8),
    ]);
    await Promise.all([
      waitForNextRoundOrCompletion(player1),
      waitForNextRoundOrCompletion(player2),
    ]);
    await player1.waitForTimeout(round < 6 ? 220 : 45);
  }

  await Promise.all([
    player1.locator("#finish-btn:not(:disabled)").waitFor({ timeout: 30_000 }),
    player2.locator("#finish-btn:not(:disabled)").waitFor({ timeout: 30_000 }),
  ]);
  await player1.screenshot({ path: `${EVIDENCE_DIR}/player1_game_complete.png` });
  await player2.screenshot({ path: `${EVIDENCE_DIR}/player2_game_complete.png` });

  const player1Signal = await player1.locator("#signal-card").textContent();
  const player2Signal = await player2.locator("#signal-card").textContent();
  console.log(JSON.stringify({
    player1OwnClicks: await ownClickCount(player1),
    player2OwnClicks: await ownClickCount(player2),
    player1Signal,
    player2Signal,
  }));

  await Promise.all([
    player1.locator("#finish-btn").click(),
    player2.locator("#finish-btn").click(),
  ]);
  await Promise.all([
    player1.getByText("The game is complete").waitFor({ timeout: 30_000 }),
    player2.getByText("The game is complete").waitFor({ timeout: 30_000 }),
  ]);
  await player1.screenshot({ path: `${EVIDENCE_DIR}/player1_completion_page.png` });
  await browser1.close();
  await browser2.close();
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
