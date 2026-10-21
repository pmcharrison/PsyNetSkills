const { chromium } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const participantUrl =
  process.env.PARTICIPANT_URL ||
  "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair";
const attemptDir = path.resolve(__dirname, "../../..");
const evidenceDir = path.join(attemptDir, "evidence", "live_scheduling");
const screenshotsDir = path.join(evidenceDir, "screenshots");
const sliderValues = [64, 128, 192, 32, 96, 160, 224, 80];
let sliderStep = 0;

fs.mkdirSync(screenshotsDir, { recursive: true });

async function visibleText(page) {
  return (await page.locator("body").innerText()).replace(/\s+/g, " ");
}

async function screenshotOnce(page, seen, key, filename) {
  if (!seen.has(key)) {
    await page.waitForTimeout(400);
    await page.screenshot({ path: path.join(screenshotsDir, filename), fullPage: true });
    seen.add(key);
  }
}

async function clickFirstAction(page) {
  const candidates = page.locator(
    "button:visible, input[type=submit]:visible, a.btn:visible, .btn:visible"
  );
  const count = await candidates.count();
  for (let index = 0; index < count; index += 1) {
    const candidate = candidates.nth(index);
    const text = (await candidate.innerText().catch(() => "")).trim();
    const value = (await candidate.getAttribute("value").catch(() => "")) || "";
    const label = `${text} ${value}`.toLowerCase();
    if (!label.includes("abort") && !label.includes("dashboard")) {
      await candidate.click();
      return true;
    }
  }
  return false;
}

async function answerSlider(page) {
  const sliders = page.locator("input[type=range]");
  const count = await sliders.count();
  if (count === 0) {
    return false;
  }
  const value = String(sliderValues[sliderStep % sliderValues.length]);
  sliderStep += 1;
  for (let index = 0; index < count; index += 1) {
    await sliders.nth(index).evaluate((element, nextValue) => {
      element.value = nextValue;
      element.dispatchEvent(new Event("input", { bubbles: true }));
      element.dispatchEvent(new Event("change", { bubbles: true }));
    }, value);
  }
  await page.waitForTimeout(150);
  return true;
}

(async () => {
  const startedAt = new Date().toISOString();
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  const seen = new Set();

  await page.goto(participantUrl, { waitUntil: "domcontentloaded" });

  for (let step = 0; step < 100; step += 1) {
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await page.waitForTimeout(500);

    if (page.url().includes("/recruiter-exit")) {
      await screenshotOnce(page, seen, "completion", "04-human-completion.png");
      break;
    }

    const text = await visibleText(page);
    if (text.includes("What participant group would you like to join?")) {
      await screenshotOnce(page, seen, "choose", "01-human-group-choice.png");
      await page.getByRole("button", { name: "A" }).click();
      continue;
    }

    if (text.includes("Adjust the slider to match")) {
      await screenshotOnce(page, seen, "trial", "02-human-color-trial.png");
      const answered = await answerSlider(page);
      if (!answered) {
        throw new Error("Color trial was visible, but no slider was found.");
      }
      await clickFirstAction(page);
      continue;
    }

    if (text.toLowerCase().includes("consistency score")) {
      await screenshotOnce(page, seen, "feedback", "03-human-feedback.png");
      await clickFirstAction(page);
      continue;
    }

    if (text.includes("Communicating with the recruiter")) {
      await page.waitForTimeout(1000);
      continue;
    }

    const clicked = await clickFirstAction(page);
    if (!clicked) {
      throw new Error(`No participant action found at ${page.url()} with text: ${text}`);
    }
  }

  const finishedAt = new Date().toISOString();
  if (!page.url().includes("/recruiter-exit")) {
    throw new Error(`Human participant did not reach recruiter exit; current URL: ${page.url()}`);
  }

  fs.writeFileSync(
    path.join(evidenceDir, "human_flow.json"),
    `${JSON.stringify(
      {
        participant_url: participantUrl,
        started_at: startedAt,
        finished_at: finishedAt,
        final_url: page.url(),
        screenshots: fs.readdirSync(screenshotsDir).sort(),
      },
      null,
      2
    )}\n`
  );

  await context.close();
  await browser.close();
})();
