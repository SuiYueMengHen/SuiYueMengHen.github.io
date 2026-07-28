import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: ({ image }) => z.object({
    title: z.string().trim().min(1),
    description: z.string().trim().min(10).max(180),
    publishDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    category: z.string().trim().min(1),
    tags: z.array(z.string().trim().min(1)).min(1),
    cover: image().optional(),
    coverAlt: z.string().optional(),
    featured: z.boolean().default(false),
    draft: z.boolean().default(false),
    series: z.string().optional(),
    canonical: z.url().optional(),
  }),
});

export const collections = { blog };
