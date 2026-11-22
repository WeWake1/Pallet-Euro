// PROTOTYPE tooling: start headless Chrome for the review scripts (Mac or Windows). Set CHROME to override.
import fs from 'node:fs';
import puppeteer from 'puppeteer-core';

const candidates = [
  process.env.CHROME,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  `${process.env.LOCALAPPDATA ?? ''}\\Google\\Chrome\\Application\\chrome.exe`,
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  '/usr/bin/google-chrome',
].filter(Boolean);

export const chromePath = candidates.find((p) => fs.existsSync(p));
export const BASE = process.env.PE_BASE ?? 'http://127.0.0.1:4322';

export function launch() {
  if (!chromePath) throw new Error('Chrome not found: set CHROME to chrome.exe (or msedge.exe)');
  return puppeteer.launch({ executablePath: chromePath, headless: 'new', args: ['--allow-file-access-from-files', '--hide-scrollbars'] });
}
