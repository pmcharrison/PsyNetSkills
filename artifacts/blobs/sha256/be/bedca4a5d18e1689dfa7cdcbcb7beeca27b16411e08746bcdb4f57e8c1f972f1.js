const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

const experimentDir = path.resolve(__dirname, "..");
const attemptDir = path.resolve(experimentDir, "../..");
const evidenceDir = path.join(attemptDir, "evidence");
const screenshotsDir = path.join(evidenceDir, "screenshots");
const baseUrl = process.env.PSYNET_BASE_URL || "http://127.0.0.1:5000";
const adUrl = `${baseUrl}/ad?generate_tokens=true&recruiter=hotair`;

test.use({
  viewport: { width: 1280, height: 720 },
  launchOptions: {
    executablePath: "/usr/bin/google-chrome",
    args: ["--no-sandbox"],
  },
});

async function clickFirstUsefulControl(page) {
  const controls = [
    page.getByRole("button", { name: /next|continue|start|begin|accept|submit|finish/i }),
    page.locator("button.push-button"),
    page.locator("input[type=submit]"),
    page.locator("a.btn"),
  ];
  for (const locator of controls) {
    if ((await locator.count()) > 0) {
      await locator.first().click();
      return;
    }
  }
  throw new Error("No useful control found on page.");
}

async function advanceToText(page, text, maxClicks = 12) {
  for (let i = 0; i < maxClicks; i += 1) {
    if ((await page.locator("body").innerText()).includes(text)) return;
    await clickFirstUsefulControl(page);
    await page.waitForLoadState("networkidle").catch(() => {});
    await page.waitForTimeout(300);
  }
  throw new Error(`Did not reach text: ${text}`);
}

async function startParticipant(page) {
  await page.goto(adUrl);
  await advanceToText(page, "Quorum personality and guessing game");
}

async function choosePersonality(page, responseLabel = "Very accurate") {
  await page.getByRole("button", { name: responseLabel }).click();
  await page.waitForTimeout(250);
}

async function submitGuess(page, value) {
  await page.locator("#sliderpage_slider").evaluate((slider, v) => {
    slider.value = String(v);
    slider.dispatchEvent(new Event("input", { bubbles: true }));
    slider.dispatchEvent(new Event("change", { bubbles: true }));
  }, value);
  await page.getByRole("button", { name: /next/i }).click();
  await page.waitForTimeout(250);
}

async function answerCurrentLobbyPage(page) {
  const text = await page.locator("body").innerText();
  if (text.includes("Guessing game")) {
    await submitGuess(page, 5);
  } else if (text.includes("Personality")) {
    await choosePersonality(page);
  } else {
    await clickFirstUsefulControl(page);
  }
}

async function advanceToQuorate(page) {
  for (let i = 0; i < 14; i += 1) {
    const text = await page.locator("body").innerText();
    if (text.includes("We are now quorate")) return;
    if (text.includes("Hidden target:")) {
      await clickFirstUsefulControl(page);
    } else {
      await answerCurrentLobbyPage(page);
    }
    await page.waitForTimeout(700);
  }
  throw new Error("Participant did not reach the quorate page.");
}

async function saveScreenshot(page, filename) {
  await page.screenshot({ path: path.join(screenshotsDir, filename), fullPage: true });
}

test("participant flow shows productive lobby and quorate release", async ({ browser }) => {
  fs.mkdirSync(screenshotsDir, { recursive: true });

  const context1 = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: path.join(experimentDir, "playwright-video"), size: { width: 1280, height: 720 } },
  });
  const context2 = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const context3 = await browser.newContext({ viewport: { width: 1280, height: 720 } });

  const p1 = await context1.newPage();
  const p2 = await context2.newPage();
  const p3 = await context3.newPage();

  await startParticipant(p1);
  await expect(p1.locator("body")).toContainText("productive waiting pages");
  await saveScreenshot(p1, "01-instructions.png");
  await clickFirstUsefulControl(p1);

  await expect(p1.locator("body")).toContainText("Waiting-room task 1 of 40: Personality");
  await expect(p1.locator("body")).toContainText("Item 1 (E1)");
  await saveScreenshot(p1, "02-personality-pushbuttons.png");

  for (let item = 1; item <= 10; item += 1) {
    await expect(p1.locator("body")).toContainText(`Item ${item}`);
    await choosePersonality(p1);
  }

  await expect(p1.locator("body")).toContainText("Waiting-room task 11 of 40: Guessing game");
  await expect(p1.locator("body")).not.toContainText("Hidden target:");
  await saveScreenshot(p1, "03-guessing-slider-hidden-target.png");
  await submitGuess(p1, 9);
  await expect(p1.locator("body")).toContainText("Feedback: Warmer");
  await saveScreenshot(p1, "04-guessing-feedback.png");
  await clickFirstUsefulControl(p1);

  await startParticipant(p2);
  await clickFirstUsefulControl(p2);
  await choosePersonality(p2, "Neither accurate nor inaccurate");

  await startParticipant(p3);
  await clickFirstUsefulControl(p3);
  await advanceToQuorate(p3);
  await advanceToQuorate(p1);

  await expect(p1.locator("body")).toContainText("This is the tutorial-style main loop");
  await saveScreenshot(p1, "05-quorate-main-loop.png");

  const manifest = {
    captions: {
      "01-instructions.png": "Instructions explain quorum release, productive waiting tasks, recording, and recovery behavior.",
      "02-personality-pushbuttons.png": "Personality lobby trial uses PsyNet push buttons with the five-point accuracy scale.",
      "03-guessing-slider-hidden-target.png": "Guessing lobby trial uses a 0-10 slider and does not show the target before submission.",
      "04-guessing-feedback.png": "Guessing feedback reveals target, guess, difference, and feedback label after submission.",
      "05-quorate-main-loop.png": "Participant is released into the tutorial-style quorate main loop once the group is quorate.",
    },
  };
  fs.writeFileSync(path.join(screenshotsDir, "manifest.json"), JSON.stringify(manifest, null, 2));

  await context2.close();
  await context3.close();
  await context1.close();

  const videoPath = await p1.video().path();
  fs.copyFileSync(videoPath, path.join(evidenceDir, "participant.webm"));
});
