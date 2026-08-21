const { chromium } = require("playwright");

const html = `
<!doctype html>
<html>
<body style="margin:0;background:#000;color:#fff;font-family:sans-serif;">
  <button id="start" style="font-size:40px;margin:80px;">Start sync probe</button>
  <script>
    const flashes = [];
    async function beepAndFlash(index) {
      document.body.style.background = "#fff";
      flashes.push(performance.now());
      const audioContext = new AudioContext();
      const oscillator = audioContext.createOscillator();
      const gain = audioContext.createGain();
      oscillator.frequency.value = 880;
      gain.gain.value = 0.35;
      oscillator.connect(gain);
      gain.connect(audioContext.destination);
      oscillator.start();
      setTimeout(() => {
        oscillator.stop();
        audioContext.close();
        document.body.style.background = "#000";
        if (index === 4) {
          document.title = "done";
          console.log("probe-done", JSON.stringify(flashes));
        }
      }, 120);
    }
    document.getElementById("start").addEventListener("click", () => {
      document.getElementById("start").remove();
      for (let index = 0; index < 5; index += 1) {
        setTimeout(() => beepAndFlash(index), 1000 + index * 1000);
      }
    });
  </script>
</body>
</html>`;

(async () => {
  const browser = await chromium.launch({
    channel: "chrome",
    headless: false,
    args: [
      "--autoplay-policy=no-user-gesture-required",
      "--window-position=0,0",
      "--window-size=1280,720",
    ],
  });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  page.on("console", (msg) => console.log(msg.text()));
  await page.setContent(html);
  await page.click("#start");
  await page.waitForFunction(() => document.title === "done", null, { timeout: 10000 });
  await page.waitForTimeout(500);
  await browser.close();
})();
