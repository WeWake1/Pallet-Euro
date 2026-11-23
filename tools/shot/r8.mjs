// Screenshots of round 8's self-moving heroes over time (dev server running): B (scenes advance), C (tap to
// transform: one tap, then the result), D (plays by itself). Prints errors and sideways overflow.
//   node tools/shot/r8.mjs <outdir> [width=1440] [height=900]
import fs from 'node:fs';
import { launch, BASE } from './browser.mjs';

const [, , out, w = '1440', h = '900'] = process.argv;
if (!out) { console.log('usage: node tools/shot/r8.mjs <outdir> [w] [h]'); process.exit(1); }
fs.mkdirSync(out, { recursive: true });
const b = await launch();
const mobile = +w <= 500;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
for (const v of ['B', 'C', 'D']) {
  const p = await b.newPage();
  await p.setViewport({ width: +w, height: +h, deviceScaleFactor: mobile ? 2 : 1, isMobile: mobile, hasTouch: mobile });
  const errs = [];
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('pageerror', (e) => errs.push('PAGEERROR ' + e.message));
  p.on('response', (r) => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url()); });
  await p.goto(`${BASE}/prototype/?variant=${v}`, { waitUntil: 'networkidle0', timeout: 60000 });
  const tag = `${v}-${mobile ? 'phone' : 'desk'}`;
  await sleep(2500);
  await p.screenshot({ path: `${out}/${tag}-1.png` });
  if (v === 'B') { await sleep(7500); await p.screenshot({ path: `${out}/${tag}-2.png` }); await sleep(7000); await p.screenshot({ path: `${out}/${tag}-3.png` }); }
  if (v === 'C') {
    await p.evaluate(() => document.querySelector('.r8-family button[data-id="epal3"]').click());
    await sleep(800); await p.screenshot({ path: `${out}/${tag}-2.png` });
    await sleep(2200); await p.screenshot({ path: `${out}/${tag}-3.png` });
  }
  if (v === 'D') { await sleep(6000); await p.screenshot({ path: `${out}/${tag}-2.png` }); }
  const overflow = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  console.log(`${tag}: ${errs.length} errors${errs.length ? ': ' + errs.slice(0, 4).join(' | ') : ''}; overflow ${overflow}px`);
  await p.close();
}
await b.close();
