#!/usr/bin/env node
import { chromium, expect } from "@playwright/test";

function parseArgs(argv) {
  const args = {
    expectedTrials: 4,
    humanTime: false,
    actionDelay: null,
    pageDelay: null,
    afterAudioDelay: null,
    beforeNextDelay: null,
    finalDelay: null,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--") && !args.url) {
      args.url = arg;
    } else if (arg === "--human-time") {
      args.humanTime = true;
    } else if (arg === "--expected-trials") {
      args.expectedTrials = Number(argv[++i]);
    } else if (arg === "--action-delay") {
      args.actionDelay = Number(argv[++i]);
    } else if (arg === "--page-delay") {
      args.pageDelay = Number(argv[++i]);
    } else if (arg === "--after-audio-delay") {
      args.afterAudioDelay = Number(argv[++i]);
    } else if (arg === "--before-next-delay") {
      args.beforeNextDelay = Number(argv[++i]);
    } else if (arg === "--final-delay") {
      args.finalDelay = Number(argv[++i]);
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!args.url) {
    printHelp();
    throw new Error("Missing participant URL.");
  }

  const defaults = {
    actionDelay: args.humanTime ? 0.6 : 0,
    pageDelay: args.humanTime ? 0.9 : 0,
    afterAudioDelay: args.humanTime ? 0.6 : 0,
    beforeNextDelay: args.humanTime ? 1.2 : 0,
    finalDelay: args.humanTime ? 2.0 : 0,
  };

  return {
    ...args,
    actionDelay: args.actionDelay ?? defaults.actionDelay,
    pageDelay: args.pageDelay ?? defaults.pageDelay,
    afterAudioDelay: args.afterAudioDelay ?? defaults.afterAudioDelay,
    beforeNextDelay: args.beforeNextDelay ?? defaults.beforeNextDelay,
    finalDelay: args.finalDelay ?? defaults.finalDelay,
  };
}

function printHelp() {
  console.log(`Usage: node scripts/playwright_participant_flow.mjs <url> [options]

Options:
  --expected-trials <n>     Expected number of sequence trials (default: 4)
  --human-time              Use slower pacing for illustrative recordings
  --action-delay <seconds>  Pause after response/action clicks
  --page-delay <seconds>    Pause after page transitions
  --after-audio-delay <s>   Pause after playback finishes before responding
  --before-next-delay <s>   Show completed response before clicking Next
  --final-delay <seconds>   Pause on final page before closing
`);
}

async function pause(page, seconds) {
  if (seconds > 0) {
    await page.waitForTimeout(seconds * 1000);
  }
}

async function clickIfVisible(page, name, { timeout = 500, delay = 0 } = {}) {
  const button = page.getByRole("button", { name }).first();
  try {
    await button.waitFor({ state: "visible", timeout });
  } catch {
    return false;
  }

  if (!(await button.isEnabled())) {
    return false;
  }

  await button.click();
  await pause(page, delay);
  return true;
}

async function enterSequenceResponse(
  page,
  { actionDelay, afterAudioDelay, beforeNextDelay },
) {
  const instruction = page.getByText(/Enter \d+ tones in order/i).first();
  await instruction.waitFor({ state: "visible", timeout: 10_000 });
  const text = await instruction.innerText();
  const match = text.match(/Enter (\d+) tones/i);
  if (!match) {
    throw new Error("Could not determine target sequence length.");
  }

  const targetLength = Number(match[1]);
  await page.getByRole("button", { name: /^Start$/i }).click();
  await page
    .locator("button.sequence-recall-button:not([disabled])")
    .first()
    .waitFor({ state: "visible", timeout: 10_000 });
  await pause(page, afterAudioDelay);

  const labels = ["Low", "Medium", "High"];
  for (let i = 0; i < targetLength; i += 1) {
    await page.getByRole("button", { name: labels[i % labels.length] }).click();
    await pause(page, actionDelay);
  }

  const responseText = await page.locator("#sequence-recall-response").innerText();
  const responseLength = responseText.split("→").length;
  if (responseLength !== targetLength) {
    throw new Error(
      `Expected ${targetLength} response tones, saw ${responseLength}: ${responseText}`,
    );
  }
  await pause(page, beforeNextDelay);
  await page.getByRole("button", { name: /^Next$/i }).click();
  await pause(page, actionDelay);
}

async function runFlow(args) {
  const chromePath = process.env.CHROME_PATH || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    executablePath: chromePath,
    headless: false,
    args: [
      "--no-sandbox",
      "--window-size=1280,720",
      "--autoplay-policy=no-user-gesture-required",
    ],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto(args.url, { waitUntil: "domcontentloaded" });
  await pause(page, args.pageDelay);

  let trialsCompleted = 0;
  let finishedClicked = false;
  for (let i = 0; i < 100; i += 1) {
    if (
      await clickIfVisible(page, /^Begin Experiment$/i, {
        timeout: 1000,
        delay: args.pageDelay,
      })
    ) {
      continue;
    }

    if (await page.getByText(/Enter \d+ tones in order/i).first().isVisible()) {
      await pause(page, args.pageDelay);
      await enterSequenceResponse(page, args);
      trialsCompleted += 1;
      continue;
    }

    if (
      await clickIfVisible(page, /^Next$/i, {
        timeout: 500,
        delay: args.pageDelay,
      })
    ) {
      continue;
    }

    if (
      await clickIfVisible(page, /^Finish$/i, {
        timeout: 500,
        delay: args.finalDelay,
      })
    ) {
      finishedClicked = true;
      break;
    }

    await page.waitForTimeout(250);
  }

  if (trialsCompleted !== args.expectedTrials) {
    throw new Error(
      `Expected ${args.expectedTrials} trials, completed ${trialsCompleted}.`,
    );
  }
  if (!finishedClicked) {
    throw new Error("Expected to click the final Finish button.");
  }
  await browser.close();
}

const args = parseArgs(process.argv.slice(2));
await runFlow(args);
