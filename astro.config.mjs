import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { unified } from '@astrojs/markdown-remark';

export default defineConfig({
  site: 'https://suiyuemenghen.github.io',
  output: 'static',
  integrations: [mdx(), sitemap()],
  markdown: {
    processor: unified({ gfm: true }),
    shikiConfig: { theme: 'github-dark-default', wrap: true },
  },
  vite: { build: { cssMinify: true } },
});
