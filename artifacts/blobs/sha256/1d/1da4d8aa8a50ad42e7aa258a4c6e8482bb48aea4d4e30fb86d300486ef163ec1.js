const { chromium } = require("@playwright/test");
const fs = require("fs");

const AD_URL =
  process.env.PARTICIPANT_URL ||
  "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair";
const CHROME = process.env.CHROME_BIN || "/usr/local/bin/google-chrome";
const GRID_SIZE = 8;
const ROUNDS = Number(process.env.EVIDENCE_ROUNDS || "4");

async function clickVisible(page, selectors) {
  for (const selector of selectors) {
    const target = page.locator(selector).first();
    if ((await target.count()) > 0 && (await target.isVisible().catch(() => false))) {
      const popupPromise = page.context().waitForEvent("page", { timeout: 1500 }).catch(() => null);
      await target.click({ timeout: 3000 }).catch(() => {});
      const popup = await popupPromise;
      if (popup) {
        await popup.waitForLoadState("domcontentloaded").catch(() => {});
        return popup;
      }
      return page;
    }
  }
  return page;
}

async function progressToGame(page, label) {
  await page.goto(AD_URL, { waitUntil: "domcontentloaded" });
  for (let step = 0; step < 30; step += 1) {
    if ((await page.locator("#own-grid").count()) > 0) return page;
    page = await clickVisible(page, [
      "#next-button",
      "a:has-text('Begin Experiment')",
      "button:has-text('Start')",
      "button:has-text('Begin')",
      "button:has-text('Next')",
      "button:has-text('Continue')",
      "a:has-text('Start')",
      "a:has-text('Begin')",
      "a:has-text('Next')",
      "a:has-text('Continue')",
      "text=Begin Experiment",
      "input[type='submit']",
      ".btn-primary",
    ]);
    await page.waitForTimeout(700);
  }
  throw new Error(`${label} did not reach the pixel game page`);
}

async function activePlayerIndex(pages) {
  const probes = pages.map(async (page, index) => {
    await page.locator(".cell:not([disabled])").first().waitFor({ timeout: 15000 });
    return index;
  });
  try {
    return await Promise.any(probes);
  } catch (error) {
    await Promise.all(
      pages.map(async (page, index) => {
        await page.screenshot({ path: `evidence/debug_timeout_p${index + 1}.png`, fullPage: true });
        console.error(`Participant ${index + 1} URL: ${page.url()}`);
        console.error(`Participant ${index + 1} text:\n${await page.locator("body").innerText().catch(() => "")}`);
      })
    );
    throw error;
  }
}

async function clickTurn(page, turnIndex) {
  const row = turnIndex % GRID_SIZE;
  const col = (turnIndex * 3) % GRID_SIZE;
  await page.locator(`.cell[data-row="${row}"][data-col="${col}"]`).click();
  await page.waitForTimeout(900);
}

async function main() {
  const sharedArgs = [
    "--no-first-run",
    "--hide-crash-restore-bubble",
    "--disable-session-crashed-bubble",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--autoplay-policy=no-user-gesture-required",
  ];
  fs.rmSync("/tmp/pixel-game-p1", { recursive: true, force: true });
  fs.rmSync("/tmp/pixel-game-p2", { recursive: true, force: true });
  const p1 = await chromium.launchPersistentContext("/tmp/pixel-game-p1", {
    headless: false,
    executablePath: CHROME,
    viewport: { width: 640, height: 720 },
    args: [...sharedArgs, "--window-size=640,720", "--window-position=0,0"],
  });
  const p2 = await chromium.launchPersistentContext("/tmp/pixel-game-p2", {
    headless: false,
    executablePath: CHROME,
    viewport: { width: 640, height: 720 },
    args: [...sharedArgs, "--window-size=640,720", "--window-position=640,0"],
  });

  const page1 = p1.pages()[0] || (await p1.newPage());
  const page2 = p2.pages()[0] || (await p2.newPage());
  const pages = [page1, page2];
  pages.forEach((page, index) => {
    page.on("console", (message) => console.log(`p${index + 1} console ${message.type()}: ${message.text()}`));
    page.on("pageerror", (error) => console.error(`p${index + 1} pageerror: ${error.message}`));
  });

  const gamePages = await Promise.all([
    progressToGame(page1, "participant 1"),
    progressToGame(page2, "participant 2"),
  ]);
  pages[0] = gamePages[0] || page1;
  pages[1] = gamePages[1] || page2;

  for (let turn = 0; turn < ROUNDS * 2; turn += 1) {
    const index = await activePlayerIndex(pages);
    await clickTurn(pages[index], turn);
  }

  await Promise.all(
    pages.map(async (page) => {
      await page.locator("#finish-button").waitFor({ state: "visible", timeout: 20000 });
      await page.locator("#finish-button").click();
      await page.waitForTimeout(1000);
    })
  );

  await page1.screenshot({ path: "evidence/player1_completion.png", fullPage: true });
  await page2.screenshot({ path: "evidence/player2_completion.png", fullPage: true });
  await p1.close();
  await p2.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
