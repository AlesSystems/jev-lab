const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const net = require('node:net');

const root = path.resolve(__dirname, '..');
const output = path.join(root, 'docs/screenshots/jev-response-studio');
const available = ['claim_check', 'field_matchmaker', 'interruption_budget', 'festival_control_room', 'launch_lab', 'feedback_kitchen', 'jev_habitat', 'demo_dashboard', 'release_room'];
const requested = process.argv.slice(2);
assert.ok(requested.every(demo => available.includes(demo)), 'Use known demo directory names');
const demos = requested.length ? requested : available;
const servers = [];
const results = [];

async function start(demo) {
  const socket = net.createServer();
  await new Promise(resolve => socket.listen(0, '127.0.0.1', resolve));
  const port = socket.address().port;
  await new Promise(resolve => socket.close(resolve));
  const child = spawn(process.env.PYTHON || 'python3', [`demos/${demo}/${demo}.py`, 'serve', '--port', String(port)], {
    cwd: root, env: { ...process.env, TYPESAFE_API_KEY: '', PYTHONDONTWRITEBYTECODE: '1' }, stdio: ['ignore', 'pipe', 'pipe'],
  });
  servers.push(child);
  let diagnostic = '';
  child.stderr.on('data', chunk => { diagnostic += chunk; });
  const url = `http://127.0.0.1:${port}`;
  for (let i = 0; i < 100; i++) {
    if (child.exitCode !== null) throw new Error(`${demo} exited: ${diagnostic}`);
    try { if ((await fetch(url)).ok) return url; } catch {}
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  throw new Error(`${demo} did not start: ${diagnostic}`);
}

async function inspect(page) {
  await page.locator('.jev-inspection').waitFor();
  await page.locator('.jev-inspection summary').click();
  assert.match(await page.locator('.jev-inspection').innerText(), /not Jev thinking|no separate written rationale/i);
}

async function exercise(page, demo) {
  if (demo === 'claim_check') {
    await page.locator('#claim').waitFor();
    await page.waitForFunction(() => document.querySelector('#claim').value.length > 0);
    await page.locator('#run').click();
    await inspect(page);
    await page.locator('#claim').fill('An edited claim');
    assert.equal(await page.locator('.jev-inspection').count(), 0);
    await page.locator('#scenarios button').first().click();
    await page.locator('#run').click();
    await inspect(page);
  } else if (demo === 'field_matchmaker') {
    await page.waitForFunction(() => document.querySelector('#csv-input').value.length > 0);
    await page.locator('#suggest').click();
    await inspect(page);
    await page.locator('#csv-input').fill('Company,Email\nExample,a@example.test');
    assert.equal(await page.locator('.jev-inspection').count(), 0);
    await page.locator('#suggest').click();
    await inspect(page);
  } else if (demo === 'interruption_budget') {
    await inspect(page);
    await page.locator('#event-text').fill('Customers cannot finish their checkout.');
    assert.equal(await page.locator('.jev-inspection').count(), 0);
    await page.locator('#sort').click();
    await page.locator('.jev-inspection').waitFor();
    await page.locator('#page').check();
    await page.locator('#sort').click();
    await page.waitForFunction(() => document.querySelector('#status').textContent.includes('Code rule'));
    await inspect(page);
    assert.match(await page.locator('#sheet').innerText(), /Attention now/i);
  } else if (demo === 'festival_control_room') {
    await page.locator('#timeline').fill('600');
    await page.locator('#timeline').dispatchEvent('input');
    await page.locator('#report-list button').first().click();
    await inspect(page);
  } else if (demo === 'launch_lab') {
    await page.locator('#releases button').first().waitFor();
    await page.locator('#assess').click();
    await page.locator('#assessment').waitFor({ state: 'visible' });
    await page.locator('#assessment summary').click();
    assert.match(await page.locator('#assessment').innerText(), /fixture/i);
    await page.locator('#evidence input').first().uncheck();
    assert.equal(await page.locator('#assessment').isHidden(), true);
    await page.locator('#assess').click();
    await page.locator('#assessment').waitFor({ state: 'visible' });
    await page.locator('#assessment summary').click();
  } else if (demo === 'feedback_kitchen') {
    await page.waitForFunction(() => document.querySelector('#inspection').textContent.length > 2);
    await page.locator('.inspect summary').click();
    assert.match(await page.locator('#inspection').innerText(), /fixture|baseline/i);
    await page.locator('#new-comment').fill('My shopping list vanishes when the connection drops.');
    await page.getByRole('button', { name: 'Add comment', exact: true }).click();
    assert.doesNotMatch(await page.locator('#inspection').innerText(), /"response"/);
    await page.locator('#products button').nth(1).click();
  } else if (demo === 'jev_habitat') {
    await page.locator('.example').first().waitFor();
    await page.locator('#evaluate').click();
    await page.locator('#result').waitFor({ state: 'visible' });
    await page.locator('.inspector summary').click();
    assert.match(await page.locator('#inspection-note').innerText(), /fixture answers|typed judgments/i);
    await page.locator('#request-text').fill('An edited request');
    assert.equal(await page.locator('#raw-response').innerText(), '');
    await page.locator('.example').first().click();
    await page.locator('#evaluate').click();
    await page.locator('#result').waitFor({ state: 'visible' });
  } else if (demo === 'release_room') {
    await page.locator('#workbench').waitFor({ state: 'visible' });
    await page.locator('#assess-feedback').click();
    await page.waitForFunction(() => document.querySelector('#feedback-status').textContent.includes('Prepared baseline'));
    assert.equal(await page.locator('.note-result').count(), 8);
    await page.locator('#pick-offline').check();
    await page.locator('#assess-release').click();
    await page.waitForFunction(() => document.querySelector('#decision').textContent === 'HOLD');
    await page.locator('#evidence-fr_retry').uncheck();
    assert.equal(await page.locator('#decision').innerText(), 'UNREAD');
    assert.equal(await page.locator('.note-result').count(), 8, 'Release edits must preserve feedback results');
    await page.locator('#assess-release').click();
    await page.waitForFunction(() => document.querySelector('#decision').textContent === 'HOLD');
    await page.locator('#note-c1').fill('The shopping list disappears offline.');
    assert.equal(await page.locator('.note-result').count(), 0);
    assert.equal(await page.locator('#decision').innerText(), 'HOLD', 'Feedback edits must preserve release results');
    await page.locator('#assess-feedback').click();
    await page.waitForFunction(() => document.querySelector('#feedback-status').classList.contains('error'));
    assert.match(await page.locator('#feedback-status').innerText(), /original comments/);
    await page.locator('#reset-feedback').click();
    await page.locator('#assess-feedback').click();
    await page.waitForFunction(() => document.querySelector('#feedback-status').textContent.includes('Prepared baseline'));
    await page.locator('#release').selectOption('midnight');
    await page.locator('#assess-release').click();
    await page.waitForFunction(() => document.querySelector('#decision').textContent === 'READY');
    assert.equal(await page.locator('#support').innerText(), '90%');
    assert.equal(await page.locator('.finding-score').count(), 6);
    for (const checkbox of await page.locator('#evidence input').all()) await checkbox.uncheck();
    await page.locator('#evidence-mi_chat').check();
    await page.locator('#assess-release').click();
    await page.waitForFunction(() => document.querySelector('#decision').textContent === 'REVIEW');
    assert.equal(await page.locator('#support').innerText(), '18%');
    await page.locator('#release-mode').selectOption('live');
    await page.locator('#assess-release').click();
    await page.waitForFunction(() => document.querySelector('#release-status').classList.contains('error'));
    assert.match(await page.locator('#release-status').innerText(), /TYPESAFE_API_KEY/);
    await page.locator('#release-mode').selectOption('fixture');
    await page.locator('#release').selectOption('friday');
    let received;
    const started = new Promise(resolve => { received = resolve; });
    let releaseResponse;
    const gate = new Promise(resolve => { releaseResponse = resolve; });
    await page.route('**/api/release', async route => {
      const response = await route.fetch();
      received();
      await gate;
      await route.fulfill({ response });
    });
    await page.locator('#assess-release').click();
    await started;
    await page.locator('#evidence-fr_retry').uncheck();
    releaseResponse();
    await page.waitForLoadState('networkidle');
    assert.equal(await page.locator('#decision').innerText(), 'UNREAD', 'Late response must remain discarded');
    assert.equal(await page.locator('#assess-release').isEnabled(), true);
    assert.doesNotMatch(await page.locator('#release-trace').innerText(), /\"answers\"/);
    await page.unroute('**/api/release');
    await page.locator('#reset-release').click();
    await page.locator('#assess-release').click();
    await page.waitForFunction(() => document.querySelector('#decision').textContent === 'HOLD');
    await page.getByText('Inspect release exchange', { exact: true }).click();
    await page.getByText('Inspect feedback exchange', { exact: true }).click();
    await page.keyboard.press('Tab');
    assert.notEqual(await page.evaluate(() => document.activeElement.tagName), 'BODY');
  } else if (demo === 'demo_dashboard') {
    await page.locator('[data-demo="release_room"]').click();
    assert.equal(await page.locator('.demo-btn').count(), 10);
    assert.match(await page.locator('h1').innerText(), /Release Room/);
    assert.equal(await page.locator('a[href="http://127.0.0.1:8770"]').count(), 1);
    await page.reload();
    await page.locator('h1').filter({ hasText: 'Release Room' }).waitFor();
  }
}

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    for (const demo of demos) {
      const url = await start(demo);
      for (const [name, width, height] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
        const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        page.setDefaultTimeout(10000);
        await page.goto(url);
        await exercise(page, demo);
        await page.evaluate(() => document.fonts.ready);
        await page.screenshot({ path: path.join(output, `${demo}-${name}.png`), fullPage: true });
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
        assert.ok(overflow <= 1, `${demo} ${name} horizontal overflow: ${overflow}px`);
        assert.deepEqual(errors, [], `${demo} ${name} browser errors`);
        await page.close();
      }
      results.push({ demo, status: 'PASS', viewports: [1440, 390] });
      console.log(`PASS ${demo}`);
    }
    fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify({ source: 'Offline servers, synthetic fixtures, Chromium', results }, null, 2) + '\n');
  } finally {
    await browser.close();
    for (const server of servers) server.kill();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
