const { test, expect } = require("@playwright/test");

const participantUrl =
  process.env.PSYNET_PARTICIPANT_URL ||
  "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair";

async function clickIfVisible(page, names) {
  for (const name of names) {
    const candidate = page.getByRole("button", { name }).first();
    if ((await candidate.count()) > 0 && (await candidate.isVisible())) {
      await candidate.click();
      return true;
    }
    const link = page.getByRole("link", { name }).first();
    if ((await link.count()) > 0 && (await link.isVisible())) {
      await link.click();
      return true;
    }
  }
  return false;
}

async function completeIshiharaPlate(page, answer) {
  const input = page.locator("input[type='text'], input:not([type]), textarea").first();
  await advanceUntilVisible(page, input, 3);
  await input.fill(answer);
  await clickIfVisible(page, [/next/i, /submit/i]);
}

async function advanceUntilVisible(page, locator, maxClicks = 5) {
  for (let attempt = 0; attempt <= maxClicks; attempt += 1) {
    if ((await locator.count()) > 0 && (await locator.first().isVisible())) {
      return;
    }
    await clickIfVisible(page, [/next/i, /continue/i, /begin experiment/i, /start/i]);
    await page.waitForTimeout(500);
  }
  await expect(locator.first()).toBeVisible();
}

test("participant can complete minimal visual discrimination flow", async ({ page }) => {
  await page.goto(participantUrl);
  await advanceUntilVisible(page, page.getByText(/colored circles/i));
  await clickIfVisible(page, [/next/i, /continue/i]);

  for (let trial = 1; trial <= 3; trial += 1) {
    await expect(page.getByText(new RegExp(`Trial ${trial} of 3`))).toBeVisible();
    await expect(page.getByText(/Same or different/i)).toBeVisible({ timeout: 8_000 });
    await page.keyboard.press(trial % 2 === 0 ? "KeyD" : "KeyS");
  }

  await expect(page.getByText(/Ishihara color vision check/i)).toBeVisible();
  await clickIfVisible(page, [/next/i, /continue/i]);

  for (const answer of ["12", "8", "29", "5", "3", "15"]) {
    await completeIshiharaPlate(page, answer);
  }

  await expect(page.getByText(/three demographic questions/i)).toBeVisible();
  await clickIfVisible(page, [/next/i, /continue/i]);

  await expect(page.getByText(/What is your age/i)).toBeVisible();
  await page.locator("input[type='number'], input[type='text'], input:not([type])").first().fill("30");
  await clickIfVisible(page, [/next/i, /submit/i]);

  await expect(page.getByText(/How do you identify yourself/i)).toBeVisible();
  const preferNot = page.getByText(/prefer not to answer/i).first();
  await preferNot.click();
  await clickIfVisible(page, [/next/i, /submit/i]);

  await expect(page.getByText(/mother tongue/i)).toBeVisible();
  const languageSelect = page.locator("select");
  const englishValue = await languageSelect.evaluate((select) => {
    const option = [...select.options].find((entry) => /English/.test(entry.text));
    return option && option.value;
  });
  expect(englishValue).toBeTruthy();
  await languageSelect.selectOption(englishValue);
  await clickIfVisible(page, [/next/i, /submit/i]);

  await expect(page.getByText(/You're finished!/i)).toBeVisible({ timeout: 15_000 });
});
