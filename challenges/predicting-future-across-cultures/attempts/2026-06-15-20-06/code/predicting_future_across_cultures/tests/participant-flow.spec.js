const { test, expect, chromium } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const adUrl = process.env.AD_URL || "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair";
const locale = process.env.EVIDENCE_LOCALE || "he";
const evidenceDir = process.env.EVIDENCE_DIR || path.resolve(__dirname, "../../../evidence");
const screenshotDir = path.join(evidenceDir, "screenshots");
const videoDir = path.join(evidenceDir, "raw-video");
const recordVideo = process.env.RECORD_VIDEO === "1";
const slowEvidence = process.env.SLOW_EVIDENCE === "1";
const stopAtDebrief = process.env.STOP_AT_DEBRIEF === "1";

async function pauseForEvidence(page, ms = 700) {
  if (slowEvidence) {
    await page.waitForTimeout(ms);
  }
}

async function dismissValidation(page) {
  const modalButton = page.getByRole("button", { name: /OK|אישור|Va bene|בסדר/i });
  if (await modalButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await pauseForEvidence(page, 1000);
    await modalButton.click();
    await pauseForEvidence(page);
  }
}

async function clickNext(page) {
  const nextById = page.locator("#next-button");
  if (await nextById.isVisible({ timeout: 2000 }).catch(() => false)) {
    await nextById.click();
  } else {
    await page.getByRole("button").first().click();
  }
  await page.waitForLoadState("networkidle").catch(() => {});
  await pauseForEvidence(page);
}

async function answerPredictionPage(page, value) {
  const input = page.locator("#number-input-container input");
  await input.waitFor({ state: "visible", timeout: 20000 });
  await input.fill(String(value));
  await pauseForEvidence(page);
  await clickNext(page);
}

test("participant flow screenshots and video evidence", async () => {
  test.setTimeout(120000);
  fs.mkdirSync(screenshotDir, { recursive: true });
  fs.mkdirSync(videoDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: recordVideo ? { dir: videoDir, size: { width: 1280, height: 720 } } : undefined,
  });
  const page = await context.newPage();

  await page.goto(adUrl, { waitUntil: "networkidle" });
  await page.getByRole("button").first().click();
  await page.waitForLoadState("networkidle").catch(() => {});

  // PsyNet's local debug flow may include a short consent/landing page before the task instructions.
  for (let i = 0; i < 3; i += 1) {
    const bodyText = await page.locator("body").innerText();
    if (
      bodyText.includes("Predicting everyday futures") ||
      bodyText.includes("Prevedere futuri quotidiani") ||
      bodyText.includes("חיזוי עתידים יומיומיים")
    ) {
      break;
    }
    await clickNext(page);
  }

  await expect(page.locator("body")).toContainText(
    locale === "it"
      ? "Prevedere futuri quotidiani"
      : locale === "he"
        ? "חיזוי עתידים יומיומיים"
        : "Predicting everyday futures"
  );
  await page.screenshot({ path: path.join(screenshotDir, `01_${locale}_instructions.png`), fullPage: true });

  await clickNext(page);
  await page.locator("#number-input-container input").waitFor({ state: "visible", timeout: 20000 });
  await page.screenshot({ path: path.join(screenshotDir, `02_${locale}_trial.png`), fullPage: true });

  await answerPredictionPage(page, 0);
  await expect(page.locator("body")).toContainText(
    locale === "it"
      ? "La tua previsione deve essere almeno"
      : locale === "he"
        ? "התחזית שלך חייבת להיות לפחות"
        : "Your prediction must be at least"
  );
  await page.screenshot({ path: path.join(screenshotDir, `03_${locale}_validation.png`), fullPage: true });
  await dismissValidation(page);

  await answerPredictionPage(page, 999);
  for (let answered = 1; answered < 5; answered += 1) {
    await answerPredictionPage(page, 999);
  }

  await expect(page.locator("body")).toContainText(
    locale === "it" ? "Grazie" : locale === "he" ? "תודה" : "Thank you"
  );
  await page.screenshot({ path: path.join(screenshotDir, `04_${locale}_debrief.png`), fullPage: true });
  if (stopAtDebrief) {
    await pauseForEvidence(page, 1500);
    await context.close();
    await browser.close();
    return;
  }
  await clickNext(page);

  await page.waitForURL(/recruiter-exit|worker_complete|complete|questionnaire/, { timeout: 30000 }).catch(() => {});
  await context.close();
  await browser.close();

  const manifestPath = path.join(screenshotDir, "manifest.json");
  const manifest = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, "utf8")) : { captions: {} };
  manifest.captions[`01_${locale}_instructions.png`] = `${locale}: localized instructions page`;
  manifest.captions[`02_${locale}_trial.png`] = `${locale}: representative prediction trial`;
  manifest.captions[`03_${locale}_validation.png`] = `${locale}: validation rejects a prediction below t_past`;
  manifest.captions[`04_${locale}_debrief.png`] = `${locale}: localized debrief page`;
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\n");
});
