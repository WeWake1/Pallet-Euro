// Screenshots of the prototype home page (dev server running), with console errors and sideways overflow.
//   node tools/shot/shots.mjs <outdir> <variant A|B|C> [width=1440] [height=900] [hero|films|all]
// Phones: width <= 500 (390 x 844 is the usual check). Films on computers are shot at several scroll points;
// on phones the script waits for the play-once film to finish. Server: PE_BASE (default http://127.0.0.1:4322).
import fs from 'node:fs';
import { launch, BASE } from './browser.mjs';

const [, , out, variant = 'A', w = '1440', h = '900', mode = 'all'] = process.argv;
if (!out) { console.log('usage: node tools/shot/shots.mjs <outdir> <variant> [w] [h] [hero|films|all]'); process.exit(1); }
fs.mkdirSync(out, { recursive: true });
const b = await launch();
const p = await b.newPage();
const mobile = +w <= 500;
await p.setViewport({ width: +w, height: +h, deviceScaleFactor: mobile ? 2 : 1, isMobile: mobile, hasTouch: mobile });
const errs = [];
p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
p.on('pageerror', (e) => errs.push('PAGEERROR ' + e.message));
p.on('response', (r) => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url()); });
await p.goto(`${BASE}/prototype/?variant=${variant}`, { waitUntil: 'networkidle0', timeout: 60000 });
await new Promise((r) => setTimeout(r, 3500));
const tag = `${variant}-${mobile ? 'phone' : 'desk'}`;
if (mode !== 'films') await p.screenshot({ path: `${out}/${tag}-hero.png` });
if (mode !== 'hero') {
  for (const id of ['the-mark', 'quote']) {
    const box = await p.evaluate((id) => { const el = document.getElementById(id); if (!el) return null; const r = el.getBoundingClientRect(); return { top: r.top + scrollY, height: el.offsetHeight }; }, id);
    if (!box) continue;
    if (!mobile) {
      for (const q of id === 'the-mark' ? [0.03, 0.15, 0.4, 0.66, 0.97] : [0.03, 0.5, 0.97]) {
        await p.evaluate((y) => window.scrollTo(0, y), box.top + q * (box.height - +h));
        await new Promise((r) => setTimeout(r, 1500));
        await p.screenshot({ path: `${out}/${tag}-${id}-${String(Math.round(q * 100)).padStart(2, '0')}.png` });
      }
    } else {
      await p.evaluate((y) => window.scrollTo(0, y), box.top - 60);
      await new Promise((r) => setTimeout(r, 12000));
      await p.screenshot({ path: `${out}/${tag}-${id}.png` });
    }
  }
}
const overflow = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
console.log(tag, 'sideways overflow', overflow, 'px, errors', errs.length);
for (const e of errs.slice(0, 12)) console.log('  ', e);
await b.close();
