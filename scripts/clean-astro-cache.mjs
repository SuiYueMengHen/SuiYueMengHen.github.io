import { rmSync } from 'node:fs';
import { resolve } from 'node:path';

for (const directory of ['.astro', 'node_modules/.astro']) {
  rmSync(resolve(directory), { recursive: true, force: true });
}

console.log('✓ Astro 内容缓存已清理');
