import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const articleSource = readFileSync(new URL('../pages/blog/[...slug].astro', import.meta.url), 'utf8');

describe('article typography', () => {
  it('renders block quotes in upright text by default', () => {
    expect(articleSource).toContain('.prose :global(blockquote){font-style:normal}');
  });
});
