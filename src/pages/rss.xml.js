import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { postSlug, visiblePosts } from '../lib/posts';
import { siteConfig } from '../config/site';

export async function GET(context) {
  const posts = visiblePosts(await getCollection('blog'));
  return rss({
    title: `${siteConfig.name} · ${siteConfig.englishName}`,
    description: siteConfig.description,
    site: context.site,
    customData: '<language>zh-CN</language>',
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.publishDate,
      link: `/blog/${postSlug(post)}/`,
      categories: [post.data.category, ...post.data.tags],
    })),
  });
}
