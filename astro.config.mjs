// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://palleteuro.com',
  trailingSlash: 'always',
  // Keep HTML-aware whitespace (Astro 7 defaults to JSX rules, which glue inline words together)
  compressHTML: true,
  integrations: [react()],
  // forwardConsole off: Vite 7 crashes the dev server while formatting some forwarded browser errors
  vite: { plugins: [tailwindcss()], server: { forwardConsole: false } },
  build: { format: 'directory', inlineStylesheets: 'auto' },
  devToolbar: { enabled: false },
});
