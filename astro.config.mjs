import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { unified } from '@astrojs/markdown-remark';
import remarkMath from 'remark-math';
import rehypeMathjax from 'rehype-mathjax/svg';
import { rehypeSourcePositions } from './src/lib/rehype-source-positions.mjs';

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
        [rehypeMathjax, {
          svg: {
            displayAlign: 'center',
            fontCache: 'local',
            internalSpeechTitles: true,
            mtextInheritFont: true,
          },
          tex: {
            processEscapes: true,
            tags: 'ams',
          },
        }],
      ],
    }),
    shikiConfig: { theme: 'github-light-default', wrap: true },
  },
  vite: { build: { cssMinify: true } },
});
