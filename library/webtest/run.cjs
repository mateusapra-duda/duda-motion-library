// Scripted web test: plays artboards of build/biblioteca.riv in headless Chromium with the site's runtime
// (@rive-app/webgl2 2.45.0, autoBind), runs timed steps (JS through window.T, canvas captures) and prints the logs.
//
// usage (a server at the repo root, e.g. `.venv/bin/python -I -m http.server 8768 --bind 127.0.0.1`):
//        WEBTEST_URL=http://localhost:8768/library/webtest/index.html node library/webtest/run.cjs PLAN.json OUT_DIR
//        with "src": "/pieces/<piece>/build/<piece>.riv" in the plan; or, for a piece, its copy's
//        scripts/webtest.py, which serves the piece and writes the plan
// PLAN: [{ "name", "ab", "w", "h", "s", "watch": "a/b,c", "steps": [{ "at": seconds, "js": "...", "shot": "label",
//          "move": [x, y], "click": [x, y], "type": "text" }] }]   (x, y in artboard points)
// Playwright: PLAYWRIGHT=/path/to/node_modules/playwright, else the repo's tools/web/node_modules (SETUP.md, optional
// step; found from library/ or from a piece's lib/ copy), else the npx cache.
const fs = require("fs");
const path = require("path");
function playwright() {
  if (process.env.PLAYWRIGHT) return process.env.PLAYWRIGHT;
  for (let d = __dirname; d !== path.dirname(d); d = path.dirname(d)) {
    const p = path.join(d, "tools", "web", "node_modules", "playwright");
    if (fs.existsSync(p)) return p;
  }
  const npx = path.join(process.env.HOME, ".npm", "_npx");
  for (const d of fs.existsSync(npx) ? fs.readdirSync(npx) : []) {
    const p = path.join(npx, d, "node_modules", "playwright");
    if (fs.existsSync(p)) return p;
  }
  return "playwright";
}
const PW = playwright();
const { chromium } = require(PW);
// a headless shell already in the Playwright cache (any revision), unless CHROME names one
function headlessShell() {
  if (process.env.CHROME) return process.env.CHROME;
  const cache = path.join(process.env.HOME, "Library/Caches/ms-playwright");
  for (const d of fs.existsSync(cache) ? fs.readdirSync(cache).sort().reverse() : []) {
    const exe = path.join(cache, d, "chrome-headless-shell-mac-arm64/chrome-headless-shell");
    if (d.startsWith("chromium_headless_shell") && fs.existsSync(exe)) return exe;
  }
  return undefined;
}

const plan = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = process.argv[3];
fs.mkdirSync(out, { recursive: true });

(async () => {
  const browser = await chromium.launch({ executablePath: headlessShell(), args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  for (const t of plan) {
    const s = t.s || 1;
    const page = await browser.newPage({ viewport: { width: Math.max(800, t.w * s + 40), height: t.h * s + 420 } });
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
    const url = `${process.env.WEBTEST_URL || "http://localhost:8773/webtest/index.html"}?ab=${encodeURIComponent(t.ab)}&w=${t.w}&h=${t.h}&s=${s}` +
      `&watch=${encodeURIComponent(t.watch || "")}&bust=${Date.now()}` + (t.src ? "&src=" + encodeURIComponent(t.src) : "");
    await page.goto(url);
    await page.waitForFunction(() => window.T && window.T.ready, null, { timeout: 30000 });
    const start = Date.now();
    console.log(`== ${t.name} (${t.ab})`);
    for (const st of t.steps) {
      const wait = st.at * 1000 - (Date.now() - start);
      if (wait > 0) await page.waitForTimeout(wait);
      if (st.move || st.click) {
        const box = await page.locator("#c").boundingBox();
        const [x, y] = st.move || st.click;
        await page.mouse.move(box.x + x * s, box.y + y * s);
        if (st.click) await page.mouse.click(box.x + x * s, box.y + y * s);
        console.log(`  ${st.at}s ${st.click ? "click" : "move"} ${x},${y}`);
      }
      if (st.type) { await page.keyboard.type(st.type, { delay: 40 }); console.log(`  ${st.at}s type ${st.type}`); }
      if (st.js) console.log(`  ${st.at}s js: ${st.js} -> ${JSON.stringify(await page.evaluate(st.js))}`);
      if (st.shot) {
        const file = path.join(out, `${t.name}_${st.shot}.png`);
        await page.locator("#c").screenshot({ path: file });
        console.log(`  ${st.at}s shot ${file}`);
      }
    }
    console.log((await page.evaluate(() => window.T.log())).split("\n").map((l) => "  | " + l).join("\n"));
    if (errors.length) console.log("  ERRORS:\n" + errors.map((e) => "  ! " + e).join("\n"));
    await page.close();
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
