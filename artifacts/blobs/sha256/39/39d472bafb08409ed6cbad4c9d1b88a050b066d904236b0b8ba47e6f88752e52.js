const { chromium } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const participantUrl =
  process.env.PARTICIPANT_URL ||
  "http://localhost:5000/ad?recruiter=hotair&generate_tokens=1&mode=debug";
const evidenceDir = path.resolve(process.env.EVIDENCE_DIR || "../../evidence");
const screenshotsDir = path.join(evidenceDir, "screenshots");
const videoDir = path.join(evidenceDir, "playwright-video");

fs.mkdirSync(screenshotsDir, { recursive: true });
fs.mkdirSync(videoDir, { recursive: true });

async function clickContinue(page) {
  await page.waitForTimeout(400);
  try {
    return await page.evaluate(() => {
      const labels = ["Begin", "Start", "Continue", "Next", "Finish"];
      const candidates = Array.from(
        document.querySelectorAll("button, a.btn, .push-button"),
      );
      for (const candidate of candidates) {
        const style = window.getComputedStyle(candidate);
        const rect = candidate.getBoundingClientRect();
        const visible =
          style.visibility !== "hidden" &&
          style.display !== "none" &&
          rect.width > 0 &&
          rect.height > 0;
        const enabled = !candidate.disabled;
        const text = candidate.textContent || "";
        const matches =
          labels.some((label) => text.includes(label)) ||
          candidate.classList.contains("push-button");
        if (visible && enabled && matches) {
          candidate.click();
          return true;
        }
      }
      return false;
    });
  } catch (error) {
    if (String(error).includes("Execution context was destroyed")) {
      return true;
    }
    throw error;
  }
}

async function advanceToMemoryTask(page) {
  for (let i = 0; i < 20; i += 1) {
    if (await page.locator("#memory-task").first().isVisible()) {
      return;
    }
    if (!(await clickContinue(page))) {
      await page.waitForTimeout(500);
    }
  }
  throw new Error("Could not reach memory task");
}

async function respondToMemoryTrial(page) {
  await page.locator("#memory-task").waitFor({ state: "visible", timeout: 15000 });
  await page.locator("#phase-title").filter({ hasText: "Reproduce" }).waitFor({
    state: "visible",
    timeout: 8000,
  });
  await page.locator("#memory-canvas").evaluate((svg) => {
    const rect = svg.getBoundingClientRect();
    svg.dispatchEvent(
      new MouseEvent("click", {
        bubbles: true,
        clientX: rect.left + rect.width / 2,
        clientY: rect.top + rect.height / 2,
      }),
    );
  });
  for (let i = 0; i < 20; i += 1) {
    const feedback = (await page.locator("#feedback").textContent()) || "";
    if (/accurate/i.test(feedback)) {
      await page.waitForTimeout(900);
      return;
    }
    await page.waitForTimeout(250);
  }
  throw new Error("Feedback did not appear after click");
}

async function submitMemoryTrial(page) {
  await page.locator("#submit-response").evaluate((button) => button.click());
  await page.waitForFunction(
    () =>
      !document.querySelector("#memory-task") ||
      !document.querySelector("#phase-title")?.textContent.includes("Reproduce"),
    null,
    { timeout: 10000 },
  );
}

(async () => {
  const browser = await chromium.launch({
    executablePath: "/usr/local/bin/google-chrome",
    headless: true,
    args: ["--no-sandbox"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();

  page.on("pageerror", (error) => {
    throw error;
  });

  await page.goto(participantUrl);

  for (let i = 0; i < 20; i += 1) {
    const text = await page.locator("body").innerText().catch(() => "");
    if (text.includes("In this experiment")) {
      break;
    }
    if (!(await clickContinue(page))) {
      await page.waitForTimeout(500);
    }
  }

  await page.screenshot({
    path: path.join(screenshotsDir, "01_instructions.png"),
    fullPage: true,
  });
  await clickContinue(page);
  await advanceToMemoryTask(page);

  await page.locator("#phase-title").filter({ hasText: "Remember" }).waitFor();
  await page.screenshot({
    path: path.join(screenshotsDir, "02_stimulus_display.png"),
    fullPage: true,
  });

  await respondToMemoryTrial(page);
  await page.screenshot({
    path: path.join(screenshotsDir, "03_response_feedback.png"),
    fullPage: true,
  });
  await submitMemoryTrial(page);

  let experimentalScreenshotTaken = false;
  for (let step = 0; step < 80; step += 1) {
    if (page.url().includes("/recruiter-exit")) {
      break;
    }
    if (await page.locator("#memory-task").first().isVisible()) {
      await respondToMemoryTrial(page);
      if (!experimentalScreenshotTaken) {
        await page.screenshot({
          path: path.join(screenshotsDir, "04_experimental_feedback.png"),
          fullPage: true,
        });
        experimentalScreenshotTaken = true;
      }
      await submitMemoryTrial(page);
    } else if (!(await clickContinue(page))) {
      await page.waitForTimeout(500);
    }
  }

  if (!page.url().includes("/recruiter-exit")) {
    throw new Error(`Participant did not finish; final URL was ${page.url()}`);
  }

  fs.writeFileSync(
    path.join(screenshotsDir, "manifest.json"),
    JSON.stringify(
      {
        captions: {
          "01_instructions.png": "Participant instructions for the dot-location memory task.",
          "02_stimulus_display.png": "Timed stimulus display with a dot inside the outline.",
          "03_response_feedback.png": "Practice response screen showing click feedback.",
          "04_experimental_feedback.png": "Experimental chain trial response screen showing feedback.",
        },
      },
      null,
      2,
    ),
  );

  const video = page.video();
  await context.close();
  if (video) {
    await video.saveAs(path.join(evidenceDir, "participant.webm"));
  }
  await browser.close();
  console.log("Participant flow completed and evidence saved.");
})();
