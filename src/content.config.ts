import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: ({ image }) =>
    z.object({
      title: z.string().trim().min(1),
      description: z.string().trim().max(180).default(''),
      publishDate: z.coerce.date(),
      updatedDate: z.coerce.date().optional(),
      tags: z.array(z.string().trim().min(1)).default([]),
      cover: image().optional(),
      coverAlt: z.string().optional(),
      draft: z.boolean().default(false),
      canonical: z.url().optional(),
    }),
});

const projects = defineCollection({
  loader: glob({ pattern: '**/*.{yaml,yml}', base: './src/content/projects' }),
  schema: z.object({
    repo: z.string().regex(/^[\w.-]+\/[\w.-]+$/),
    title: z.string().trim().min(1),
    description: z.string().trim(),
    language: z.string().nullable().optional(),
    stars: z.number().int().nonnegative().default(0),
    forks: z.number().int().nonnegative().default(0),
    license: z.string().nullable().optional(),
    topics: z.array(z.string()).default([]),
    homepage: z.url().nullable().optional(),
    cover: z.string().trim().optional(),
    coverAlt: z.string().trim().optional(),
    featured: z.boolean().default(false),
    order: z.number().int().nonnegative().default(100),
    syncedAt: z.coerce.date(),
  }),
});

export const collections = { blog, projects };
