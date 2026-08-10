import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const articleSource = readFileSync(new URL('../pages/blog/[...slug].astro', import.meta.url), 'utf8');

describe('article typography', () => {
  it('renders block quotes in upright text by default', () => {
    expect(articleSource).toContain('.prose :global(blockquote){font-style:normal}');
  });

  it('uses the same atomic inline-math wrapper in both article directories', () => {
    expect(articleSource.match(/toc-inline-math math-source math-source--inline/g)).toHaveLength(2);
    expect(articleSource).toContain(".toc-inline-math :global(mjx-container:not([display='true'])){display:inline-block!important");
  });
});
