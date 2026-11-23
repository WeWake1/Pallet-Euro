// Screenshots of the anatomy viewer (/prototype/inner/?variant=A, dev server running): assembled, taken apart,
// pointing at a part, a layer picked, turned by dragging. Prints console errors and sideways overflow.
//   node tools/shot/anatomy.mjs <outdir> [width=1440] [height=900]
import fs from 'node:fs';
import { launch, BASE } from './browser.mjs';

const [, , out, w = '1440', h = '900'] = process.argv;
if (!out) { console.log('usage: node tools/shot/anatomy.mjs <outdir> [w] [h]'); process.exit(1); }
fs.mkdirSync(out, { recursive: true });
const b = await launch();
const p = await b.newPage();
const mobile = +w <= 500;
await p.setViewport({ width: +w, height: +h, deviceScaleFactor: mobile ? 2 : 1, isMobile: mobile, hasTouch: mobile });
const errs = [];
p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
p.on('pageerror', (e) => errs.push('PAGEERROR ' + e.message));
p.on('response', (r) => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url()); });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const tag = mobile ? 'phone' : 'desk';
await p.goto(`${BASE}/prototype/inner/?variant=A`, { waitUntil: 'networkidle0', timeout: 60000 });
await p.evaluate(() => document.querySelector('.anatomy [data-stage]').scrollIntoView({ block: 'center', behavior: 'instant' }));
await sleep(2500);
await p.screenshot({ path: `${out}/${tag}-1-assembled.png` });
await p.click('[data-toggle]');
await sleep(3200);
await p.evaluate(() => document.querySelector('.anatomy [data-stage]').scrollIntoView({ block: 'center', behavior: 'instant' }));
await sleep(600);
await p.screenshot({ path: `${out}/${tag}-2-apart.png` });
// point at the middle of a top deck board (id 18) on the picture
const pt = await p.evaluate(() => {
  const el = document.querySelector('.anatomy .hit path[data-id="18"]');
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { x: r.left + r.width * 0.5, y: r.top + r.height * 0.5 };
});
if (pt) { if (mobile) await p.touchscreen.tap(pt.x, pt.y); else await p.mouse.move(pt.x, pt.y, { steps: 3 }); }
await sleep(700);
await p.screenshot({ path: `${out}/${tag}-3-part.png` });
await p.mouse.move(5, 5);
await p.evaluate(() => document.querySelectorAll('.anatomy .lbtn')[2].click());
await sleep(900);
await p.evaluate(() => document.querySelector('.anatomy [data-stage]').scrollIntoView({ block: 'center', behavior: 'instant' }));
await sleep(400);
await p.screenshot({ path: `${out}/${tag}-4-layer.png` });
const box = await p.evaluate(() => { const r = document.querySelector('.anatomy [data-stage]').getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; });
await p.mouse.move(box.x + box.w * 0.6, box.y + box.h * 0.85);
await p.mouse.down();
await p.mouse.move(box.x + box.w * 0.25, box.y + box.h * 0.85, { steps: 12 });
await p.mouse.up();
await sleep(1200);
await p.screenshot({ path: `${out}/${tag}-5-turned.png` });
const overflow = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
console.log(`${tag}: ${errs.length} errors${errs.length ? ': ' + errs.join(' | ') : ''}; overflow ${overflow}px; part found: ${!!pt}`);
await b.close();
