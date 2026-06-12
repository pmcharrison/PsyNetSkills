const fs = require("fs");
const path = require("path");
const { chromium, expect } = require("@playwright/test");

const baseDir = path.resolve(__dirname, "..");
const evidenceDir = path.resolve(baseDir, "../../evidence");
const screenshotDir = path.join(evidenceDir, "screenshots");
const chromePath = fs.existsSync("/usr/local/bin/google-chrome")
  ? "/usr/local/bin/google-chrome"
  : "/usr/bin/google-chrome-stable";
const adUrl =
  process.env.PSYNET_PARTICIPANT_URL ||
  "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair";

fs.mkdirSync(screenshotDir, { recursive: true });

async function clickPrimary(page, labelPattern = /^(Begin Experiment|Next|Finish)$/) {
  const button = page.getByRole("button", { name: labelPattern }).first();
  await expect(button).toBeVisible({ timeout: 15000 });
  await button.click();
}

async function screenshot(page, filename) {
  await page.screenshot({ path: path.join(screenshotDir, filename), fullPage: true });
}

async function targetString(page) {
  const target = page.locator('p[style*="monospace"]').first();
  await expect(target).toBeVisible({ timeout: 15000 });
  return (await target.textContent()).trim().replace(/\s+/g, "");
}

async function main() {
  const headless = process.env.PLAYWRIGHT_HEADLESS !== "0";
  const browser = await chromium.launch({
    executablePath: chromePath,
    headless,
    slowMo: headless ? 0 : 180,
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
  });
  const page = await context.newPage();

  await page.goto(adUrl, { waitUntil: "networkidle" });
  await expect(page.getByText("Thanks for your interest")).toBeVisible();
  await screenshot(page, "01_ad_page.png");
  await clickPrimary(page, /Begin Experiment/);

  await expect(page.getByText("To proceed")).toBeVisible();
  await screenshot(page, "02_consent.png");
  await clickPrimary(page, /Next/);

  await expect(page.getByRole("heading", { name: "Digit memory task" })).toBeVisible();
  await screenshot(page, "03_instructions.png");
  await clickPrimary(page, /Next/);

  const selectedLengths = [];
  for (let trial = 1; trial <= 10; trial += 1) {
    await expect(page.getByRole("heading", { name: `Trial ${trial} of 10` })).toBeVisible({
      timeout: 20000,
    });
    const target = await targetString(page);
    selectedLengths.push(target.length);
    if (trial === 1 || trial === 10) {
      await screenshot(page, `${String(3 + trial).padStart(2, "0")}_trial_${trial}_target.png`);
    }
    await clickPrimary(page, /Next/);

    await expect(page.getByRole("heading", { name: `Trial ${trial} of 10` })).toBeVisible();
    await expect(page.getByText(`Type the ${target.length}-digit string`)).toBeVisible();

    if (trial === 1) {
      const input = page.locator("input[type='text'], textarea").first();
      await input.fill("123");
      await clickPrimary(page, /Next/);
      await expect(page.locator("#alert-modal")).toContainText(
        `exactly ${target.length} digits`
      );
      await screenshot(page, "05_recall_validation.png");
      await page.getByRole("button", { name: "OK" }).click();
    }

    const input = page.locator("input[type='text'], textarea").first();
    await expect(input).toBeVisible();
    await input.fill(target);
    if (trial === 1) {
      await screenshot(page, "06_recall_response.png");
    }
    await clickPrimary(page, /Next/);
  }

  for (let i = 0; i < 4; i += 1) {
    if (page.url().includes("/recruiter-exit")) {
      break;
    }
    const next = page.getByRole("button", { name: /^(Next|Finish)$/ }).first();
    if (await next.isVisible().catch(() => false)) {
      await next.click();
      await page.waitForTimeout(500);
    } else {
      break;
    }
  }

  await screenshot(page, "07_completion.png");
  if (!page.url().includes("/recruiter-exit")) {
    await expect(page.getByText(/finished|performance score|Thank you/i)).toBeVisible();
  }

  await context.close();
  await browser.close();

  fs.writeFileSync(
    path.join(screenshotDir, "manifest.json"),
    JSON.stringify(
      {
        selected_lengths: selectedLengths,
        captions: {
          "01_ad_page.png": "Debug recruiter ad page.",
          "02_consent.png": "Consent handoff page.",
          "03_instructions.png": "Digit-memory task instructions.",
          "04_trial_1_target.png": "First adaptive target display.",
          "05_recall_validation.png": "Recall page after validation check.",
          "06_recall_response.png": "Recall response page with exact target entry.",
          "13_trial_10_target.png": "Final target display after adaptive updates.",
          "07_completion.png": "Completion or recruiter exit state.",
        },
      },
      null,
      2
    ) + "\n"
  );

  console.log(`Completed participant flow with lengths: ${selectedLengths.join(", ")}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
