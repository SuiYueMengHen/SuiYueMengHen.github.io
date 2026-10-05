import type { CollectionEntry } from 'astro:content';

export type BlogPost = CollectionEntry<'blog'>;
export type Project = CollectionEntry<'projects'>;

export function postSlug(post: BlogPost): string {
  return post.id.replace(/\/(index\.(md|mdx))$/, '').replace(/\.(md|mdx)$/, '');
}

export function visiblePosts(
  posts: BlogPost[],
  includeDrafts = false,
): BlogPost[] {
  return posts
    .filter((post) => includeDrafts || !post.data.draft)
    .sort(
      (a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf(),
    );
}

export function sortedProjects(items: Project[]): Project[] {
  return [...items].sort(
    (a, b) =>
      a.data.order - b.data.order ||
      a.data.title.localeCompare(b.data.title, 'zh-CN'),
  );
}

function readableText(body = ''): string {
  return body
    .replace(/^---\s*[\s\S]*?\s*---/, ' ')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]+\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[#>*_`~|{}[\]\\]/g, ' ');
}

export function contentStats(body = ''): { words: number; minutes: number } {
  const text = readableText(body);
  const chinese = (text.match(/[\u3400-\u9fff]/g) || []).length;
  const latin =
    text
      .replace(/[\u3400-\u9fff]/g, ' ')
      .match(/[\p{Letter}\p{Number}]+(?:['’\-][\p{Letter}\p{Number}]+)*/gu)
      ?.length ?? 0;
  return {
    words: chinese + latin,
    minutes: Math.max(1, Math.ceil(chinese / 300 + latin / 220)),
  };
}

export function wordCount(body = ''): number {
  return contentStats(body).words;
}
export function readingMinutes(body = ''): number {
  return contentStats(body).minutes;
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

export function slugify(input: string): string {
  return (
    input
      .trim()
      .toLowerCase()
      .replace(/[^\p{Letter}\p{Number}]+/gu, '-')
      .replace(/^-|-$/g, '') || 'untitled'
  );
}
