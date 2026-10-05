import { describe, expect, it } from 'vitest';
import type { BlogPost, Project } from './posts';
import {
  contentStats,
  readingMinutes,
  slugify,
  sortedProjects,
  visiblePosts,
  wordCount,
} from './posts';

const makePost = (
  id: string,
  date: string,
  overrides: Record<string, unknown> = {},
) =>
  ({
    id,
    body: '',
    collection: 'blog',
    data: {
      title: id,
      description: 'description long enough',
      publishDate: new Date(date),
      tags: ['界面'],
      draft: false,
      ...overrides,
    },
  }) as unknown as BlogPost;

describe('post utilities', () => {
  it('creates stable slugs', () =>
    expect(slugify('Hello, Prism Notes!')).toBe('hello-prism-notes'));
  it('keeps Chinese characters in slugs', () =>
    expect(slugify('第一篇 文章')).toBe('第一篇-文章'));
  it('estimates mixed-language reading time', () => {
    expect(readingMinutes('这是一段中文。')).toBe(1);
    expect(readingMinutes('word '.repeat(500))).toBe(3);
    expect(wordCount('棱镜 notes 2026')).toBe(4);
    expect(contentStats('![封面](./cover.png)\n正文 text')).toEqual({
      words: 3,
      minutes: 1,
    });
  });
  it('filters drafts and sorts newest first', () => {
    const posts = [
      makePost('old', '2025-01-01'),
      makePost('draft', '2027-01-01', { draft: true }),
      makePost('new', '2026-01-01'),
    ];
    expect(visiblePosts(posts).map((post) => post.id)).toEqual(['new', 'old']);
  });
  it('sorts cached project snapshots without network access', () => {
    const projects = [
      { id: 'b', data: { title: 'B', order: 2 } },
      { id: 'a', data: { title: 'A', order: 1 } },
    ] as Project[];
    expect(sortedProjects(projects).map((item) => item.id)).toEqual(['a', 'b']);
  });
});
