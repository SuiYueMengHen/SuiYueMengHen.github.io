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
    autoNumbering: z.boolean().default(true),
    showContents: z.boolean().default(true),
    showSideToc: z.boolean().default(true),
    series: z.string().optional(),
    collection: z.string().trim().min(1).optional(),
    collectionOrder: z.number().int().positive().optional(),
    canonical: z.url().optional(),
  }),
});

const bookCollections = defineCollection({
  loader: glob({ pattern: '**/*.{yaml,yml}', base: './src/content/collections' }),
  schema: z.object({
    title: z.string().trim().min(1), description: z.string().trim().min(1), order: z.number().int().positive(),
    subtitle: z.string().trim().optional(), volume: z.string().trim().optional(), cover: z.string().trim().optional(), coverAlt: z.string().trim().optional(),
    status: z.enum(['ongoing', 'complete', 'paused']).default('ongoing'), featured: z.boolean().default(false),
  }),
});

const projects = defineCollection({
  loader: glob({ pattern: '**/*.{yaml,yml}', base: './src/content/projects' }),
  schema: z.object({
    repo: z.string().regex(/^[\w.-]+\/[\w.-]+$/), title: z.string().trim().min(1), description: z.string().trim(),
    language: z.string().nullable().optional(), stars: z.number().int().nonnegative().default(0), forks: z.number().int().nonnegative().default(0), license: z.string().nullable().optional(),
    topics: z.array(z.string()).default([]), homepage: z.url().nullable().optional(), cover: z.string().trim().optional(), coverAlt: z.string().trim().optional(),
    featured: z.boolean().default(false), order: z.number().int().nonnegative().default(100), syncedAt: z.coerce.date(),
  }),
});

export const collections = { blog, collections: bookCollections, projects };
