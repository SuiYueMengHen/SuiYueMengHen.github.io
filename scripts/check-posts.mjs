import fs from 'node:fs';
import path from 'node:path';
const root = path.join(process.cwd(), 'src/content/blog');
const files = fs
  .readdirSync(root, { recursive: true, encoding: 'utf8' })
  .filter((file) => /\.(md|mdx)$/.test(file));
const errors = [];
for (const file of files) {
  const source = fs.readFileSync(path.join(root, file), 'utf8');
  const front = source.match(/^---\r?\n([\s\S]*?)\r?\n---/)?.[1];
  if (!front) {
    errors.push(`${file}: 缺少 frontmatter`);
    continue;
  }
  for (const key of ['title', 'publishDate'])
    if (!new RegExp(`^${key}:\\s*.+`, 'm').test(front))
      errors.push(`${file}: 缺少 ${key}`);
  for (const image of source.matchAll(/!\[([^\]]*)\]\((\.\/[^)\s]+)[^)]*\)/g)) {
    if (!image[1].trim()) errors.push(`${file}: 图片缺少替代文本`);
    if (!fs.existsSync(path.resolve(root, path.dirname(file), image[2])))
      errors.push(`${file}: 图片不存在 ${image[2]}`);
  }
}
if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`✓ ${files.length} 篇 Markdown 文章检查通过`);
