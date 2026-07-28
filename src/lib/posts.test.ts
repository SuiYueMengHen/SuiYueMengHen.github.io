import { describe, expect, it } from 'vitest';
import type { BlogPost } from './posts';
import { readingMinutes, relatedPosts, slugify, visiblePosts } from './posts';

const makePost = (id: string, date: string, overrides: Record<string, unknown> = {}) => ({
  id,
  body: '',
  collection: 'blog',
  data: { title: id, description: 'description long enough', publishDate: new Date(date), category: '设计', tags: ['界面'], featured: false, draft: false, ...overrides },
}) as unknown as BlogPost;

describe('post utilities', () => {
  it('creates stable slugs', () => expect(slugify('Hello, Prism Notes!')).toBe('hello-prism-notes'));
  it('keeps Chinese characters in slugs', () => expect(slugify('第一篇 文章')).toBe('第一篇-文章'));
  it('estimates mixed-language reading time', () => {
    expect(readingMinutes('这是一段中文。')).toBe(1);
    expect(readingMinutes('word '.repeat(500))).toBe(3);
  });
  it('filters drafts and sorts newest first', () => {
    const posts = [makePost('old', '2025-01-01'), makePost('draft', '2027-01-01', { draft: true }), makePost('new', '2026-01-01')];
    expect(visiblePosts(posts).map((post) => post.id)).toEqual(['new', 'old']);
  });
  it('ranks related posts by shared tags and category', () => {
    const current = makePost('current', '2026-01-01', { tags: ['界面', '设计'] });
    const strong = makePost('strong', '2025-01-01', { tags: ['界面', '设计'] });
    const weak = makePost('weak', '2026-02-01', { tags: ['其他'] });
    expect(relatedPosts(current, [current, weak, strong]).map((post) => post.id)).toEqual(['strong', 'weak']);
  });
});
