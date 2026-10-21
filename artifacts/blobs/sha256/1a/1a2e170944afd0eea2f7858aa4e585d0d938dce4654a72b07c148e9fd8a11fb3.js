const { chromium } = require("@playwright/test");

const url =
  process.env.PARTICIPANT_URL ||
  "http://localhost:5000/ad?recruiter=hotair&generate_tokens=1&mode=debug";

async function clickIfVisible(page, label) {
  const candidates = [
    page.getByRole("button", { name: label, exact: false }),
    page.getByRole("link", { name: label, exact: false }),
    page.locator(`input[type=submit][value*="${label}"]`),
  ];
  for (const candidate of candidates) {
    if ((await candidate.count()) > 0 && (await candidate.first().isVisible())) {
      await candidate.first().click({ timeout: 3000 });
      return true;
    }
  }
  return false;
}

async function advanceToDeliberation(page) {
  for (let i = 0; i < 40; i += 1) {
    const text = await page.locator("body").innerText({ timeout: 5000 });
    if (text.includes("Deliberate with your partner")) return;

    for (const label of [
      "Begin Experiment",
      "Begin experiment",
      "I consent",
      "I agree",
      "Next",
      "Continue",
      "Start",
    ]) {
      if (await clickIfVisible(page, label)) {
        await page.waitForTimeout(500);
        break;
      }
    }
    await page.waitForTimeout(500);
  }
  throw new Error("Participant did not reach deliberation page");
}

async function launchParticipant(name, x) {
  const context = await chromium.launchPersistentContext(
    `/tmp/${name}-${Date.now()}`,
    {
    headless: false,
    executablePath: "/usr/local/bin/google-chrome",
    viewport: null,
    args: [
      `--window-position=${x},0`,
      "--window-size=640,720",
      "--no-first-run",
      "--disable-infobars",
    ],
    }
  );
  const page = context.pages()[0] || (await context.newPage());
  await page.goto(url, { waitUntil: "domcontentloaded" });
  return { context, page };
}

(async () => {
  const left = await launchParticipant("rps-chat-left", 0);
  const right = await launchParticipant("rps-chat-right", 640);

  await Promise.all([
    advanceToDeliberation(left.page),
    advanceToDeliberation(right.page),
  ]);

  await left.page.locator("#chatroom-chat-input").fill("Let's coordinate: I will choose rock.");
  await left.page.locator("#chatroom-send-btn").click();
  await right.page.locator("#chatroom-chat-input").fill("Got it. I will choose paper so we can verify scoring.");
  await right.page.locator("#chatroom-send-btn").click();

  await left.page.waitForTimeout(65000);
  await Promise.all([
    left.page.getByRole("button", { name: "rock" }).click(),
    right.page.getByRole("button", { name: "paper" }).click(),
  ]);

  await left.page.waitForTimeout(5000);
  await right.page.waitForTimeout(5000);

  await left.context.close();
  await right.context.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
