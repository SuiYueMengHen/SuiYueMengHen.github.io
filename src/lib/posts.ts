import type { CollectionEntry } from 'astro:content';

export type BlogPost = CollectionEntry<'blog'>;
export type BookCollection = CollectionEntry<'collections'>;
export type Project = CollectionEntry<'projects'>;

export function postSlug(post: BlogPost): string {
  return post.id.replace(/\/(index\.(md|mdx))$/, '').replace(/\.(md|mdx)$/, '');
}

export function visiblePosts(posts: BlogPost[], includeDrafts = false): BlogPost[] {
  return posts
    .filter((post) => includeDrafts || !post.data.draft)
    .sort((a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf());
}

export function sortedCollections(items: BookCollection[]): BookCollection[] {
  return [...items].sort((a, b) => a.data.order - b.data.order || a.data.title.localeCompare(b.data.title, 'zh-CN'));
}

export function collectionPosts(posts: BlogPost[], collectionId: string): BlogPost[] {
  return visiblePosts(posts).filter((post) => post.data.collection === collectionId)
    .sort((a, b) => (a.data.collectionOrder ?? Number.MAX_SAFE_INTEGER) - (b.data.collectionOrder ?? Number.MAX_SAFE_INTEGER));
}

export function uncollectedByCategory(posts: BlogPost[]): Array<[string, BlogPost[]]> {
  const shelves = new Map<string, BlogPost[]>();
  for (const post of visiblePosts(posts).filter((item) => !item.data.collection)) { const items = shelves.get(post.data.category) ?? []; items.push(post); shelves.set(post.data.category, items); }
  return [...shelves.entries()].sort(([a], [b]) => a.localeCompare(b, 'zh-CN')).map(([category, items]) => [category, items.sort((a, b) => a.data.title.localeCompare(b.data.title, 'zh-CN'))]);
}

export function categoryPosts(posts: BlogPost[], category: string): BlogPost[] {
  return visiblePosts(posts).filter((post) => post.data.category === category).sort((a, b) => a.data.title.localeCompare(b.data.title, 'zh-CN'));
}

export function adjacentPosts(current: BlogPost, ordered: BlogPost[]) { const index = ordered.findIndex((post) => post.id === current.id); return { previous: index > 0 ? ordered[index - 1] : undefined, next: index >= 0 && index < ordered.length - 1 ? ordered[index + 1] : undefined }; }

export function sortedProjects(items: Project[]): Project[] { return [...items].sort((a, b) => a.data.order - b.data.order || a.data.title.localeCompare(b.data.title, 'zh-CN')); }

export function validateCollectionAssignments(posts: Array<Pick<BlogPost, 'id' | 'data'>>, collectionIds: Set<string>): string[] {
  const errors: string[] = []; const used = new Map<string, string>();
  for (const post of posts) { const collection = post.data.collection; const order = post.data.collectionOrder;
    if (collection && !collectionIds.has(collection)) errors.push(`${post.id}: invalid collection ${collection}`);
    if (collection && (!Number.isInteger(order) || (order ?? 0) <= 0)) errors.push(`${post.id}: invalid collectionOrder`);
    if (!collection && order !== undefined) errors.push(`${post.id}: collectionOrder without collection`);
    if (collection && order) { const key = `${collection}:${order}`; if (used.has(key)) errors.push(`${post.id}: duplicate ${key}`); else used.set(key, post.id); }
  } return errors;
}

export function readingMinutes(body = ''): number {
  const chinese = (body.match(/[\u3400-\u9fff]/g) || []).length;
  const latin = body.replace(/[\u3400-\u9fff]/g, ' ').trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.ceil(chinese / 300 + latin / 220));
}

export function relatedPosts(current: BlogPost, posts: BlogPost[], limit = 3): BlogPost[] {
  return visiblePosts(posts)
    .filter((post) => post.id !== current.id)
    .map((post) => ({
      post,
      score: post.data.tags.filter((tag) => current.data.tags.includes(tag)).length * 2
        + Number(post.data.category === current.data.category),
    }))
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score || b.post.data.publishDate.valueOf() - a.post.data.publishDate.valueOf())
    .slice(0, limit)
    .map(({ post }) => post);
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }).format(date);
}

export function slugify(input: string): string {
  return input.trim().toLowerCase().replace(/[^\p{Letter}\p{Number}]+/gu, '-').replace(/^-|-$/g, '') || 'untitled';
}
