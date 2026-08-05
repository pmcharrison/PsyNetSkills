const fs = require("fs");
const path = require("path");
const { expect, test } = require("@playwright/test");

const locale = process.env.LOCALE || "en";
const participantUrl =
  process.env.PARTICIPANT_URL ||
  "http://localhost:5000/ad?recruiter=hotair&generate_tokens=1&mode=debug";
const evidenceDir =
  process.env.EVIDENCE_DIR ||
  path.resolve(__dirname, "../../../evidence/screenshots");
const evidenceDelayMs = Number(process.env.EVIDENCE_DELAY_MS || 0);

const expectedText = {
  en: {
    welcome: "Welcome",
    instructions: "Instructions",
    trial: "Trial",
    chooseA: "Choose Option A",
    thanks: "Thank you",
  },
  hi: {
    welcome: "स्वागत है",
    instructions: "निर्देश",
    trial: "परीक्षण",
    chooseA: "विकल्प A चुनें",
    thanks: "धन्यवाद",
  },
  fr: {
    welcome: "Bienvenue",
    instructions: "Instructions",
    trial: "Essai",
    chooseA: "Choisir l’option A",
    thanks: "Merci",
  },
};

test.use({
  channel: "chrome",
  viewport: { width: 1280, height: 720 },
  launchOptions: {
    args: ["--no-sandbox"],
  },
});

async function clickPrimary(page) {
  const nextButton = page.locator(
    "button:visible, input[type=submit]:visible, a.btn:visible"
  ).first();
  await expect(nextButton).toBeVisible();
  await nextButton.click();
}

async function evidencePause(page) {
  if (evidenceDelayMs > 0) {
    await page.waitForTimeout(evidenceDelayMs);
  }
}

async function saveScreenshot(page, name) {
  fs.mkdirSync(evidenceDir, { recursive: true });
  await page.screenshot({
    path: path.join(evidenceDir, `${locale}-${name}.png`),
    fullPage: true,
  });
}

test(`participant flow works in ${locale}`, async ({ page }) => {
  test.setTimeout(90_000);
  const text = expectedText[locale];
  if (!text) {
    throw new Error(`Unsupported locale for participant-flow evidence: ${locale}`);
  }

  await page.goto(participantUrl, { waitUntil: "domcontentloaded" });
  await expect(page.locator("#begin-button")).toBeVisible();
  await saveScreenshot(page, "ad");
  await evidencePause(page);
  await page.locator("#begin-button").click();

  await expect(page.locator("#consent")).toBeVisible();
  await evidencePause(page);
  await page.locator("#consent").click();

  await expect(page.locator("body")).toContainText(text.welcome);
  await saveScreenshot(page, "welcome");
  await evidencePause(page);
  await clickPrimary(page);

  await expect(page.locator("body")).toContainText(text.instructions);
  await saveScreenshot(page, "instructions");
  await evidencePause(page);
  await clickPrimary(page);

  for (let trial = 1; trial <= 6; trial += 1) {
    await expect(page.locator("body")).toContainText(text.trial);
    await expect(page.locator("body")).toContainText("0.");
    await expect(page.locator("#option_a")).toContainText(text.chooseA);
    if (trial === 1) {
      await saveScreenshot(page, "choice");
    }
    await evidencePause(page);
    await page.locator(trial % 2 === 0 ? "#option_b" : "#option_a").click();
  }

  await expect(page.locator("body")).toContainText(text.thanks);
  await saveScreenshot(page, "thanks");
  await evidencePause(page);
  await clickPrimary(page);

  await expect(page.locator("#Finish")).toBeVisible();
  await saveScreenshot(page, "finish");
  await evidencePause(page);
  await page.locator("#Finish").click();
  await page.waitForURL(/recruiter-exit|dashboard|\/ad/, { timeout: 30_000 }).catch(() => {});

  fs.mkdirSync(evidenceDir, { recursive: true });
  fs.writeFileSync(
    path.join(evidenceDir, `${locale}-completion-url.txt`),
    `${page.url()}\n`,
    "utf8"
  );
});
