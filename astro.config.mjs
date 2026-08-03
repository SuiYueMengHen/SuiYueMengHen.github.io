import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { unified } from '@astrojs/markdown-remark';
import remarkMath from 'remark-math';
import { rehypeSourcePositions } from './src/lib/rehype-source-positions.mjs';
import { rehypeResponsiveMedia } from './src/lib/rehype-responsive-media.mjs';
import { rehypeClientMath } from './src/lib/rehype-client-math.mjs';

export default defineConfig({
  site: 'https://suiyuemenghen.github.io',
  output: 'static',
  integrations: [mdx(), sitemap()],
  markdown: {
    processor: unified({
      gfm: true,
      remarkPlugins: [remarkMath],
      rehypePlugins: [
        rehypeSourcePositions,
        rehypeResponsiveMedia,
        rehypeClientMath,
      ],
    }),
    shikiConfig: {
      themes: {
        light: 'github-light-default',
        dark: 'github-dark-default',
      },
      wrap: true,
    },
  },
  vite: { build: { cssMinify: true } },
});
