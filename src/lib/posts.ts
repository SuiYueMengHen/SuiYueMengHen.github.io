import type { CollectionEntry } from 'astro:content';

export type BlogPost = CollectionEntry<'blog'>;

export function postSlug(post: BlogPost): string {
  return post.id.replace(/\/(index\.(md|mdx))$/, '').replace(/\.(md|mdx)$/, '');
}

export function visiblePosts(posts: BlogPost[], includeDrafts = false): BlogPost[] {
  return posts
    .filter((post) => includeDrafts || !post.data.draft)
    .sort((a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf());
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
