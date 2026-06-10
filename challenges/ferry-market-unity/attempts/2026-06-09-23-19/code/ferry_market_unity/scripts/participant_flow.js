const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const participantUrl = process.argv[2] || process.env.PARTICIPANT_URL;
if (!participantUrl) {
  console.error("Usage: node scripts/participant_flow.js <participant-ad-url>");
  process.exit(2);
}

const outputPath = process.env.ACTION_LOG || path.resolve(__dirname, "../../evidence/participant-actions.json");
const chromePath = process.env.CHROME_PATH || "/usr/local/bin/google-chrome";
const headed = process.env.HEADED === "1";
const slowMo = Number(process.env.SLOW_MO_MS || (headed ? 250 : 50));
const gameTimeoutMs = Number(process.env.GAME_TIMEOUT_MS || 120000);

const defaultActions = [
  { type: "clickCanvas", x: 0.50, y: 0.50, label: "focus canvas" },
  {
    type: "driveToFerry",
    steps: 180,
    sideEvery: 10,
    waitMs: 150,
    label: "move mostly forward with occasional side corrections",
  },
];

const actions = process.env.FERRY_MARKET_ACTIONS
  ? JSON.parse(process.env.FERRY_MARKET_ACTIONS)
  : defaultActions;

const log = [];
function record(event, detail = {}) {
  const entry = { at: new Date().toISOString(), event, ...detail };
  log.push(entry);
  console.log(JSON.stringify(entry));
}

async function clickIfVisible(page, selectors, label, timeout = 2500) {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    try {
      await locator.waitFor({ state: "visible", timeout });
      await locator.click();
      record("click", { label, selector });
      return true;
    } catch (error) {
      // Try the next selector.
    }
  }
  return false;
}

async function advanceUntilCanvas(page) {
  const canvas = page.locator("#unity-canvas");
  const deadline = Date.now() + 90000;
  while (Date.now() < deadline) {
    if (await canvas.count()) {
      try {
        await canvas.waitFor({ state: "visible", timeout: 1000 });
        return canvas;
      } catch (error) {
        // Continue advancing pages.
      }
    }

    const advanced = await clickIfVisible(
      page,
      [
        "text=/Begin Experiment/i",
        "text=/I agree/i",
        "text=/I consent/i",
        "text=/Consent/i",
        "text=/Next/i",
        "text=/Continue/i",
        "text=/Start/i",
        "button:has-text('Begin')",
        "button:has-text('Next')",
        "button:has-text('Continue')",
        "button:has-text('Start')",
        "input[type=submit]",
      ],
      "advance toward Unity canvas",
      1000
    );

    if (!advanced) {
      await page.keyboard.press("Enter").catch(() => {});
      record("press", { key: "Enter", label: "fallback advance" });
      await page.waitForTimeout(1000);
    }
  }
  throw new Error("Timed out before Unity canvas became visible");
}

async function runCanvasActions(page, canvas) {
  await canvas.waitFor({ state: "visible", timeout: 60000 });
  await page.waitForTimeout(3000);
  for (const action of actions) {
    const box = await canvas.boundingBox();
    if (!box) throw new Error("Unity canvas has no bounding box");
    if (action.type === "clickCanvas") {
      const x = box.x + box.width * action.x;
      const y = box.y + box.height * action.y;
      await page.mouse.click(x, y);
      record("canvas-click", { label: action.label, x: action.x, y: action.y });
      await page.waitForTimeout(action.waitMs || 500);
    } else if (action.type === "key") {
      const repeats = action.repeats || 1;
      for (let i = 0; i < repeats; i += 1) {
        await page.keyboard.press(action.key);
        await page.waitForTimeout(action.waitMs || 80);
      }
      record("key", { label: action.label, key: action.key, repeats });
    } else if (action.type === "driveToFerry") {
      const steps = action.steps || 120;
      const sideEvery = action.sideEvery || 10;
      let sidePresses = 0;
      let forwardPresses = 0;
      for (let i = 1; i <= steps; i += 1) {
        const key =
          i % sideEvery === 0
            ? (Math.floor(i / sideEvery) % 2 === 0 ? "ArrowLeft" : "ArrowRight")
            : "ArrowUp";
        await page.keyboard.press(key);
        if (key === "ArrowUp") {
          forwardPresses += 1;
        } else {
          sidePresses += 1;
        }
        if (i % 30 === 0) {
          const box = await canvas.boundingBox();
          if (box) {
            await page.mouse.click(box.x + box.width * 0.5, box.y + box.height * 0.5);
            record("canvas-click", { label: "periodic center click while driving", x: 0.5, y: 0.5, step: i });
          }
        }
        await page.waitForTimeout(action.waitMs || 120);
      }
      record("drive-to-ferry", { label: action.label, steps, forwardPresses, sidePresses });
    } else {
      throw new Error(`Unknown action type: ${action.type}`);
    }
  }
}

async function waitForCompletion(page) {
  const completion = page.locator("text=/finished|complete|thank you/i").first();
  try {
    await completion.waitFor({ state: "visible", timeout: gameTimeoutMs });
    record("completion", { text: await completion.textContent().catch(() => null) });
    return true;
  } catch (error) {
    record("completion-timeout", { timeoutMs: gameTimeoutMs });
    return false;
  }
}

(async () => {
  const browser = await chromium.launch({
    executablePath: chromePath,
    headless: !headed,
    slowMo,
    args: ["--no-sandbox", "--autoplay-policy=no-user-gesture-required", "--disable-dev-shm-usage"],
  });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  page.on("console", (message) => record("browser-console", { type: message.type(), text: message.text() }));
  page.on("pageerror", (error) => record("browser-page-error", { message: error.message }));

  try {
    record("goto", { url: participantUrl });
    await page.goto(participantUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
    const canvas = await advanceUntilCanvas(page);
    record("unity-canvas-visible");
    await runCanvasActions(page, canvas);
    const completed = await waitForCompletion(page);
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify({ completed, actions: log }, null, 2));
    await browser.close();
    process.exit(completed ? 0 : 1);
  } catch (error) {
    record("runner-error", { message: error.message, stack: error.stack });
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify({ completed: false, actions: log }, null, 2));
    await browser.close();
    process.exit(1);
  }
})();
