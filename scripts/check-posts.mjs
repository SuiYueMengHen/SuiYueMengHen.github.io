import fs from 'node:fs';
import path from 'node:path';

const root = path.join(process.cwd(), 'src/content/blog');
const files = fs.readdirSync(root, { recursive: true, encoding: 'utf8' }).filter((file) => /(?:^|\/)index\.(md|mdx)$/.test(file));
const errors = [];
const slugs = new Set();
const required = ['title', 'description', 'publishDate', 'category', 'tags'];
for (const relative of files) {
  const file = path.join(root, relative);
  const source = fs.readFileSync(file, 'utf8');
  const match = source.match(/^---\n([\s\S]*?)\n---/);
  if (!match) { errors.push(`${relative}: 缺少 frontmatter`); continue; }
  for (const key of required) if (!new RegExp(`^${key}:\\s*.+`, 'm').test(match[1])) errors.push(`${relative}: 缺少 ${key}`);
  const slug = path.dirname(relative);
  if (slugs.has(slug)) errors.push(`${relative}: slug 重复`); slugs.add(slug);
  const date = match[1].match(/^publishDate:\s*(.+)$/m)?.[1]?.trim();
  if (date && Number.isNaN(Date.parse(date))) errors.push(`${relative}: publishDate 无效`);
  for (const image of source.matchAll(/!\[[^\]]*\]\((\.\/[^)\s]+)[^)]*\)/g)) {
    if (!fs.existsSync(path.resolve(path.dirname(file), image[1]))) errors.push(`${relative}: 图片不存在 ${image[1]}`);
  }
}
if (errors.length) { console.error(errors.map((item) => `✗ ${item}`).join('\n')); process.exit(1); }
console.log(`✓ ${files.length} 篇文章检查通过`);
