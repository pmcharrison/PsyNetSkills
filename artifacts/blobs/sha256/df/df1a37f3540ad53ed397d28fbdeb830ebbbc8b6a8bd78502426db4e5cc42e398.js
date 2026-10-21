const { chromium, expect } = require("@playwright/test");

async function clickNext(page) {
  await page.getByRole("button", { name: "Next" }).click();
  await page.waitForTimeout(700);
}

(async () => {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 250,
    args: ["--window-size=1280,720", "--window-position=0,0"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });

  await page.goto(
    "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair",
    { waitUntil: "domcontentloaded" }
  );

  await expect(page.getByText("Begin Experiment")).toBeVisible();
  await page.waitForTimeout(1000);
  await page.getByText("Begin Experiment").click();

  await expect(page.getByRole("button", { name: "Next" })).toBeVisible();
  await clickNext(page);

  await expect(page.getByText("Welcome!")).toBeVisible();
  await page.waitForTimeout(1200);
  await clickNext(page);

  for (const [color, rating] of [
    ["red", "3"],
    ["green", "5"],
    ["blue", "7"],
  ]) {
    await expect(
      page.getByText(`How pleasant is this color? (${color})`)
    ).toBeVisible();
    await page.waitForTimeout(1200);
    await page.getByText(rating, { exact: true }).click();
    await page.waitForTimeout(500);
    await clickNext(page);
  }

  await expect(page.getByText("Thank you for rating the colors!")).toBeVisible();
  await page.waitForTimeout(1800);
  await browser.close();
})();
