import { describe, expect, it } from 'vitest';
import type { BlogPost, BookCollection, Project } from './posts';
import { adjacentPosts, categoryPosts, collectionPosts, contentStats, readingMinutes, relatedPosts, slugify, sortedCollections, sortedProjects, uncollectedByCategory, validateCollectionAssignments, visiblePosts, wordCount } from './posts';

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
    expect(wordCount('棱镜 notes 2026')).toBe(4);
    expect(contentStats('![封面](./cover.png)\n正文 text')).toEqual({ words: 3, minutes: 1 });
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
  it('sorts collections and chapters by explicit order', () => {
    const collections=[{id:'second',data:{title:'乙',order:2}},{id:'first',data:{title:'甲',order:1}}] as BookCollection[];
    const posts=[makePost('b','2026-01-02',{collection:'first',collectionOrder:2}),makePost('a','2026-01-01',{collection:'first',collectionOrder:1})];
    expect(sortedCollections(collections).map(item=>item.id)).toEqual(['first','second']);expect(collectionPosts(posts,'first').map(item=>item.id)).toEqual(['a','b']);
  });
  it('groups loose essays by category and Chinese title',()=>{const posts=[makePost('z','2026-01-01',{title:'乙',category:'随笔'}),makePost('a','2026-01-02',{title:'甲',category:'随笔'}),makePost('book','2026-01-03',{collection:'x',collectionOrder:1})];expect(uncollectedByCategory(posts)[0][1].map(item=>item.data.title)).toEqual(['甲','乙'])});
  it('keeps category navigation stable and adjacent',()=>{const posts=[makePost('b','2026-01-01',{title:'乙'}),makePost('a','2026-01-02',{title:'甲'})];const ordered=categoryPosts(posts,'设计');expect(ordered.map(item=>item.id)).toEqual(['a','b']);expect(adjacentPosts(ordered[1],ordered).previous?.id).toBe('a')});
  it('sorts cached project snapshots without network access',()=>{const projects=[{id:'b',data:{title:'B',order:2}},{id:'a',data:{title:'A',order:1}}] as Project[];expect(sortedProjects(projects).map(item=>item.id)).toEqual(['a','b'])});
  it('rejects invalid collection references and duplicate chapter numbers',()=>{const posts=[makePost('a','2026-01-01',{collection:'missing',collectionOrder:1}),makePost('b','2026-01-02',{collection:'book',collectionOrder:2}),makePost('c','2026-01-03',{collection:'book',collectionOrder:2})];expect(validateCollectionAssignments(posts,new Set(['book']))).toEqual(expect.arrayContaining([expect.stringContaining('invalid collection missing'),expect.stringContaining('duplicate book:2')]))});
});
