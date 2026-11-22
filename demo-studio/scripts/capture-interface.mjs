import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const [mode, root] = process.argv.slice(2);
const viewport = { width: Number(process.env.CAPTURE_WIDTH || 960), height: Number(process.env.CAPTURE_HEIGHT || 500) };
const descriptor = path.join(root, '.build/ui-capture', `${mode}.json`);
let config;
for (let attempt = 0; attempt < 240; attempt++) {
  try { config = JSON.parse(await fs.readFile(descriptor, 'utf8')); break; }
  catch { await new Promise(resolve => setTimeout(resolve, 500)); }
}
if (!config) throw Error('Webots did not start the live interface bridge');
const directory = path.join(root, '.build/ui-capture', `${mode}-frames`);
await fs.mkdir(directory, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  ...(process.env.CAPTURE_CHROMIUM ? { executablePath: process.env.CAPTURE_CHROMIUM } : {}),
});
const page = await browser.newPage({ viewport, deviceScaleFactor: 2 });
await page.addInitScript(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const cursor = document.createElement('div');
    cursor.style.cssText = 'position:fixed;left:-40px;top:-40px;width:24px;height:28px;pointer-events:none;z-index:10000;';
    cursor.innerHTML = '<svg width="24" height="28" viewBox="0 0 24 28"><path d="M2 2 L2 23 L8 17 L12 26 L16 24 L12 15 L21 15 Z" fill="#222" stroke="white" stroke-width="2"/></svg>';
    document.body.append(cursor);
    document.addEventListener('mousemove', event => {
      cursor.style.left = `${event.clientX}px`; cursor.style.top = `${event.clientY}px`;
    });
    document.addEventListener('mousedown', () => {
      cursor.style.filter = 'drop-shadow(0 0 5px #d28c24)';
      setTimeout(() => { cursor.style.filter = ''; }, 350);
    });
  });
});
const errors = [];
page.on('pageerror', error => errors.push(error.message));
await page.goto(`${config.url}/plugins/robot_windows/lockbox_window/lockbox_window.html?capture=${config.token}`);
await page.waitForFunction(() => window.captureReady);
const schedule = Object.entries(config.schedule).map(([frame, [action, data]]) => ({ frame: Number(frame), action, data }));
const trace = [];
let imageIndex = 0;
for (let frame = 0; frame < config.frames; frame++) {
  for (const item of schedule) {
    const before = frame - item.frame;
    if (before === -30) {
      await page.evaluate(() => window.scrollTo(0, 0));
      if (item.action === 'access') {
        if (await page.locator('details').getAttribute('open') !== null) await page.locator('summary').click();
        await page.locator('#role').selectOption(item.data.role);
        await page.locator('#code').fill('');
        await page.locator('#code').focus();
      } else if (item.action !== 'close') {
        if (await page.locator('details').getAttribute('open') === null) await page.locator('summary').click();
        if (item.action === 'reset_logic') await page.locator('#courier-ttl').fill(String(item.data.courier_ttl_s ?? 300));
      }
    }
    if (item.action === 'access' && [-24, -18, -12, -6].includes(before)) {
      await page.locator('#code').pressSequentially(item.data.code[([-24, -18, -12, -6]).indexOf(before)]);
    }
    if (before === 0) {
      if (!['access', 'close'].includes(item.action) && await page.locator('details').getAttribute('open') === null)
        await page.locator('summary').click();
      const button = item.action === 'access' ? page.locator('#access-form button') : page.locator(`[data-action="${item.action}"]`);
      await button.click();
      await page.evaluate(() => window.pendingCommand);
      trace.push({ frame, time_s: (frame - 8) * .032, action: item.action, role: item.data.role ?? null });
    }
    const nextTestSoon = schedule.some(next => next.frame > frame && next.frame - frame <= 30 && !['access', 'close'].includes(next.action));
    if (before === 18 && item.action !== 'access' && item.action !== 'close' && !nextTestSoon) {
      if (await page.locator('details').getAttribute('open') !== null) await page.locator('summary').click();
      await page.evaluate(() => window.scrollTo(0, 0));
    }
  }
  const result = await fetch(`${config.url}/capture/step`, { method: 'POST', headers: { 'X-Capture-Token': config.token } });
  if (!result.ok) throw Error(`Simulator step ${frame} failed: ${await result.text()}`);
  if (frame >= 8 && (frame - 8) % 3 === 0) {
    await page.evaluate(() => window.refreshStatus());
    await page.screenshot({ path: path.join(directory, `${String(++imageIndex).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 92 });
  }
  if (frame % 100 === 0) console.log(`${mode}: ${frame}/${config.frames} simulator steps, ${imageIndex} interface frames`);
}
await browser.close();
if (errors.length) throw Error(errors.join('\n'));
await fs.writeFile(path.join(root, 'results', `${mode}_interface_capture.json`), JSON.stringify({
  passed: true, source: 'Live project control page connected to the running Webots controller',
  viewport: { ...viewport, scale: 2 }, screenshot_interval_sim_s: .096,
  screenshots: imageIndex, commands: trace, browser_errors: errors,
}, null, 2) + '\n');
