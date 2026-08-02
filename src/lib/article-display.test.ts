import { describe, expect, it } from 'vitest';
import { articleDisplaySettings, articleTocHeadings } from './article-display';

describe('article display settings', () => {
  it('keeps every reading aid enabled for legacy articles', () => {
    expect(articleDisplaySettings({})).toEqual({
      autoNumbering: true,
      showContents: true,
      showSideToc: true,
    });
  });

  it('allows every option to be switched independently', () => {
    expect(articleDisplaySettings({ autoNumbering: false, showContents: true, showSideToc: false }))
      .toEqual({ autoNumbering: false, showContents: true, showSideToc: false });
  });

  it('keeps headings in both TOCs when numbering is disabled', () => {
    const headings = [
      { depth: 2, slug: 'one', text: '一' },
      { depth: 3, slug: 'one-one', text: '一点一' },
      { depth: 4, slug: 'one-one-one', text: '一点一点一' },
    ];
    expect(articleTocHeadings(headings, true).map(({ number }) => number))
      .toEqual(['第1章', '§1.1', '§1.1.1']);
    expect(articleTocHeadings(headings, false).map(({ text, number }) => [text, number]))
      .toEqual([['一', ''], ['一点一', ''], ['一点一点一', '']]);
  });
});
