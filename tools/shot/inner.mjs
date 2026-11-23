// Screenshots of the inner-pages prototype (/prototype/inner/, dev server running), with console errors and
// sideways overflow. A: hovers a deck board, then a parts-table row. B: moves the seam to 30% and 70%.
//   node tools/shot/inner.mjs <outdir> [width=1440] [height=900]
import fs from 'node:fs';
import { launch, BASE } from './browser.mjs';

const [, , out, w = '1440', h = '900'] = process.argv;
if (!out) { console.log('usage: node tools/shot/inner.mjs <outdir> [w] [h]'); process.exit(1); }
fs.mkdirSync(out, { recursive: true });
const b = await launch();
const mobile = +w <= 500;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
for (const v of ['A', 'B']) {
  const p = await b.newPage();
  await p.setViewport({ width: +w, height: +h, deviceScaleFactor: mobile ? 2 : 1, isMobile: mobile, hasTouch: mobile });
  const errs = [];
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('pageerror', (e) => errs.push('PAGEERROR ' + e.message));
  p.on('response', (r) => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url()); });
  await p.goto(`${BASE}/prototype/inner/?variant=${v}`, { waitUntil: 'networkidle0', timeout: 60000 });
  await sleep(1500);
  const tag = `${v}-${mobile ? 'phone' : 'desk'}`;
  const sel = v === 'A' ? '.inspect [data-stage]' : '[data-cmp]';
  await p.evaluate((s) => document.querySelector(s).scrollIntoView({ block: 'center', behavior: 'instant' }), sel);
  await sleep(800);   // measure only after the page has stopped scrolling
  const box = await p.evaluate((s) => { const r = document.querySelector(s).getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; }, sel);
  if (v === 'A') {
    for (const [name, fx, fy] of [['deck', 0.42, 0.42], ['mark', 0.36, 0.82]]) {
      if (mobile) await p.touchscreen.tap(box.x + box.w * fx, box.y + box.h * fy);
      else await p.mouse.move(box.x + box.w * fx, box.y + box.h * fy, { steps: 4 });
      await sleep(700);
      await p.screenshot({ path: `${out}/${tag}-${name}.png` });
    }
    if (!mobile) {
      const row = await p.evaluate(() => { const r = document.querySelectorAll('.inspect tbody tr')[2].getBoundingClientRect(); return { x: r.left + 40, y: r.top + r.height / 2 }; });
      await p.mouse.move(row.x, row.y, { steps: 4 });
      await sleep(700);
      await p.screenshot({ path: `${out}/${tag}-row.png` });
    }
  } else {
    for (const fx of [0.3, 0.7]) {
      if (mobile) {
        await p.evaluate((v) => { const i = document.querySelector('[data-cmp] input'); i.value = String(v); i.dispatchEvent(new Event('input')); }, fx * 100);
      } else await p.mouse.move(box.x + box.w * fx, box.y + box.h * 0.5, { steps: 6 });
      await sleep(900);
      await p.screenshot({ path: `${out}/${tag}-${Math.round(fx * 100)}.png` });
    }
  }
  const overflow = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  console.log(`${tag}: ${errs.length} errors${errs.length ? ': ' + errs.join(' | ') : ''}; overflow ${overflow}px`);
  await p.close();
}
await b.close();
