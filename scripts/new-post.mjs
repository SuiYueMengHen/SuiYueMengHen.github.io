import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const titleIndex = args.indexOf('--title');
const title = titleIndex >= 0 ? args[titleIndex + 1] : args.filter((item) => !item.startsWith('--')).join(' ');
if (!title) {
  console.error('用法：npm run post:new -- --title "文章标题"');
  process.exit(1);
}
const slug = title.toLowerCase().normalize('NFKC').replace(/[^\p{Letter}\p{Number}]+/gu, '-').replace(/^-|-$/g, '') || `note-${Date.now()}`;
const directory = path.join(process.cwd(), 'src/content/blog', slug);
if (fs.existsSync(directory)) {
  console.error(`文章目录已存在：${directory}`);
  process.exit(1);
}
fs.mkdirSync(directory, { recursive: true });
const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai' }).format(new Date());
const content = `---\ntitle: ${JSON.stringify(title)}\ndescription: "请用一到两句话概括文章内容，建议 30—80 字。"\npublishDate: ${today}\ncategory: "随笔"\ntags: ["待整理"]\nfeatured: false\ndraft: true\n---\n\n在这里开始写作。\n\n## 第一个小节\n\n正文内容。\n`;
fs.writeFileSync(path.join(directory, 'index.md'), content);
console.log(`已创建草稿：src/content/blog/${slug}/index.md`);
console.log('下一步：npm run dev');
