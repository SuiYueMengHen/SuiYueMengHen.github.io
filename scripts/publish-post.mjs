import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
const slug = process.argv[2];
if (!slug) { console.error('用法：npm run post:publish -- <slug>'); process.exit(1); }
const file = path.join(process.cwd(), 'src/content/blog', slug, 'index.md');
if (!fs.existsSync(file)) { console.error(`找不到文章：${file}`); process.exit(1); }
const source = fs.readFileSync(file, 'utf8');
if (!/^draft:\s*true\s*$/m.test(source)) { console.log('文章已经处于发布状态。'); }
else { fs.writeFileSync(file, source.replace(/^draft:\s*true\s*$/m, 'draft: false')); console.log(`已发布：${slug}`); }
const result = spawnSync('npm', ['run', 'post:check'], { stdio: 'inherit' });
process.exit(result.status ?? 1);
