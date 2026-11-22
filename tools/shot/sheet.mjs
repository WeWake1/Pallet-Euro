// Contact sheet of rendered frames, to review a render at a glance.
//   node tools/shot/sheet.mjs <folder> <out.png> [columns=3] [width=1800] [filename regex]
//   e.g. node tools/shot/sheet.mjs public/dev/r5/mark sheet.png 3 1800 "^(000|040|080|120|167)\."
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { launch } from './browser.mjs';

const [, , dir, out, cols = '3', width = '1800', filt = ''] = process.argv;
if (!dir || !out) { console.log('usage: node tools/shot/sheet.mjs <folder> <out.png> [cols] [width] [regex]'); process.exit(1); }
const re = filt ? new RegExp(filt) : null;
const files = fs.readdirSync(dir).filter((f) => /\.(webp|png|jpg)$/.test(f) && (!re || re.test(f))).sort();
const html = `<html><body style="margin:0;background:#888;display:grid;grid-template-columns:repeat(${cols},1fr);gap:4px;font:12px sans-serif">` +
  files.map((f) => `<figure style="margin:0;position:relative"><img src="${pathToFileURL(path.resolve(dir, f))}" style="width:100%;display:block"><figcaption style="position:absolute;left:4px;top:4px;background:#000;color:#fff;padding:2px 5px">${f}</figcaption></figure>`).join('') + '</body></html>';
const tmp = path.resolve(path.dirname(out), '_sheet.html');
fs.writeFileSync(tmp, html);
const b = await launch();
const p = await b.newPage();
await p.setViewport({ width: +width, height: 400 });
await p.goto(pathToFileURL(tmp).href, { waitUntil: 'networkidle0' });
await p.screenshot({ path: out, fullPage: true });
await b.close();
fs.unlinkSync(tmp);
console.log('sheet', out, files.length, 'images');
