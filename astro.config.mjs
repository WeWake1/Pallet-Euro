// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  // The domain is not confirmed yet (round 2, question 1): canonical URLs, the sitemap and the schema use it.
  site: 'https://palleteuro.com',
  trailingSlash: 'always',
  // Keep HTML-aware whitespace (Astro 7 defaults to JSX rules, which glue inline words together)
  compressHTML: true,
  integrations: [react(), sitemap({ filter: (page) => !/\/(prototype|404)\//.test(page) })],
  // forwardConsole off: Vite 7 crashes the dev server while formatting some forwarded browser errors
  vite: { plugins: [tailwindcss()], server: { forwardConsole: false } },
  // CSS inlined into each page: no render-blocking stylesheet request on phones (Lighthouse mobile 99–100)
  build: { format: 'directory', inlineStylesheets: 'always' },
  devToolbar: { enabled: false },
});
