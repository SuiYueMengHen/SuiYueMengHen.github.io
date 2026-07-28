import type { APIRoute } from 'astro';
import { siteConfig } from '../config/site';
export const GET: APIRoute = () => new Response(`User-agent: *\nAllow: /\nSitemap: ${siteConfig.site}/sitemap-index.xml\n`, { headers: { 'Content-Type': 'text/plain' } });
