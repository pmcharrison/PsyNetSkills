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
const canvasTimeoutMs = Number(process.env.CANVAS_TIMEOUT_MS || 180000);
const maxDriveCycles = Number(process.env.MAX_DRIVE_CYCLES || 6);

const defaultActions = [
  { type: "clickCanvas", x: 0.50, y: 0.50, label: "focus canvas" },
  {
    type: "driveToFerry",
    steps: 2500,
    sideEvery: 10,
    waitMs: 5,
    label: "rapid ArrowUp movement with 10 percent side corrections",
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
  const deadline = Date.now() + canvasTimeoutMs;
  while (Date.now() < deadline) {
    if (await canvas.count()) {
      try {
        await canvas.waitFor({ state: "attached", timeout: 1000 });
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
  record("canvas-selector-timeout", { timeoutMs: canvasTimeoutMs });
  return null;
}

async function runCanvasActions(page, canvas) {
  if (canvas) {
    await canvas.waitFor({ state: "attached", timeout: 60000 });
  }
  const cdp = await page.context().newCDPSession(page);
  const keyCodes = {
    ArrowUp: 38,
    ArrowLeft: 37,
    ArrowRight: 39,
  };
  async function dispatchArrowKey(key) {
    const code = keyCodes[key];
    await cdp.send("Input.dispatchKeyEvent", {
      type: "keyDown",
      key,
      code: key,
      windowsVirtualKeyCode: code,
      nativeVirtualKeyCode: code,
    });
    await cdp.send("Input.dispatchKeyEvent", {
      type: "keyUp",
      key,
      code: key,
      windowsVirtualKeyCode: code,
      nativeVirtualKeyCode: code,
    });
  }
  await page.waitForTimeout(3000);
  for (const action of actions) {
    let box = null;
    if (canvas) {
      box = await canvas.boundingBox();
      const boxDeadline = Date.now() + 30000;
      while (!box && Date.now() < boxDeadline) {
        await page.waitForTimeout(500);
        box = await canvas.boundingBox();
      }
    }
    if (!box) {
      const viewport = page.viewportSize() || { width: 1280, height: 720 };
      box = {
        x: Math.max(0, (viewport.width - 960) / 2),
        y: Math.max(0, (viewport.height - 600) / 2),
        width: Math.min(960, viewport.width),
        height: Math.min(600, viewport.height),
      };
      record("canvas-bounding-box-fallback", box);
    }
    if (action.type === "clickCanvas") {
      const x = box.x + box.width * action.x;
      const y = box.y + box.height * action.y;
      await page.mouse.click(x, y);
      record("canvas-click", { label: action.label, x: action.x, y: action.y });
      await page.waitForTimeout(action.waitMs || 500);
    } else if (action.type === "key") {
      const repeats = action.repeats || 1;
      for (let i = 0; i < repeats; i += 1) {
        await dispatchArrowKey(action.key);
        await page.waitForTimeout(action.waitMs || 80);
      }
      record("key", { label: action.label, key: action.key, repeats });
    } else if (action.type === "driveToFerry") {
      const steps = action.steps || 120;
      const sideEvery = action.sideEvery || 10;
      let sidePresses = 0;
      let forwardPresses = 0;
      for (let i = 1; i <= steps; i += 1) {
        if (i % sideEvery === 0) {
          const sideKey = Math.floor(i / sideEvery) % 2 === 0 ? "ArrowLeft" : "ArrowRight";
          await dispatchArrowKey(sideKey);
          sidePresses += 1;
        } else {
          await dispatchArrowKey("ArrowUp");
          forwardPresses += 1;
        }
        await page.waitForTimeout(action.waitMs || 20);
      }
      record("drive-to-ferry", { label: action.label, steps, forwardPresses, sidePresses });
    } else {
      throw new Error(`Unknown action type: ${action.type}`);
    }
  }
}

async function waitForCompletion(page, timeout = gameTimeoutMs) {
  const completion = page.locator("text=/finished|complete|thank you/i").first();
  try {
    await completion.waitFor({ state: "visible", timeout });
    record("completion", { text: await completion.textContent().catch(() => null) });
    return true;
  } catch (error) {
    record("completion-timeout", { timeoutMs: timeout });
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
    record(canvas ? "unity-canvas-attached" : "unity-canvas-fallback");
    let completed = false;
    for (let cycle = 1; cycle <= maxDriveCycles; cycle += 1) {
      record("drive-cycle-start", { cycle, maxDriveCycles });
      await runCanvasActions(page, canvas);
      completed = await waitForCompletion(page, 5000);
      if (completed) break;
    }
    if (!completed) {
      completed = await waitForCompletion(page, gameTimeoutMs);
    }
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
