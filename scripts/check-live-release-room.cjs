const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const url = process.argv[2] || 'http://127.0.0.1:8770';
assert.ok(['127.0.0.1', 'localhost'].includes(new URL(url).hostname), 'Use the local Release Room server');
const output = path.resolve(__dirname, '../docs/screenshots/jev-response-studio');
(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url);
    await page.locator('#workbench').waitFor({ state: 'visible' });
    const evidence = [];
    for (const kind of ['feedback', 'release']) {
      await page.locator(`#${kind}-mode`).selectOption('live');
      const received = page.waitForResponse(response => response.url().endsWith(`/api/${kind}`), { timeout: 45000 });
      await page.locator(`#assess-${kind}`).click();
      const response = await received;
      assert.equal(response.status(), 200, `${kind} live call`);
      const result = await response.json();
      await page.waitForFunction(kind => document.querySelector(`#${kind}-status`).textContent.includes('Live Jev'), kind);
      const displayed = JSON.parse(await page.locator(`#${kind}-trace`).textContent());
      assert.deepEqual(displayed, result.inspection, `${kind} rendered exchange must match server response`);
      assert.ok(displayed.response.model);
      assert.ok(Object.keys(displayed.response.answers).length > 0);
      evidence.push({ stage: kind, source: 'Authenticated live Jev', model: displayed.response.model, answers: Object.keys(displayed.response.answers).length, displayedExchangeMatches: true });
      await page.getByText(`Inspect ${kind} exchange`, { exact: true }).click();
    }
    assert.equal(await page.locator('#decision').innerText(), 'HOLD');
    assert.deepEqual(errors, []);
    await page.screenshot({ path: path.join(output, 'release_room-live-desktop.png'), fullPage: true });
    await page.locator('#release-trace').evaluate(el => el.scrollTop = el.scrollHeight);
    await page.locator('.release .exchange').screenshot({ path: path.join(output, 'release_room-live-response.png') });
    fs.writeFileSync(path.join(output, 'live-results.json'), JSON.stringify({ source: 'Synthetic Pantry & Co. feedback and Friday Checkout, authenticated API', results: evidence, decision: 'HOLD', noPageErrors: true }, null, 2) + '\n');
    console.log(JSON.stringify(evidence));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
