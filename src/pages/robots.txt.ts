// robots.txt follows the launch gate: before launch it blocks every crawler; after launch it allows all and
// points to the sitemap.
import type { APIRoute } from 'astro';
import { LAUNCHED } from '../data/site';

export const GET: APIRoute = ({ site }) => {
  const body = LAUNCHED
    ? `User-agent: *\nAllow: /\n\nSitemap: ${new URL('/sitemap-index.xml', site).href}\n`
    : 'User-agent: *\nDisallow: /\n';
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
