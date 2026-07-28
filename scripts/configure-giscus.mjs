import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const [owner, name] = 'SuiYueMengHen/SuiYueMengHen.github.io'.split('/');
const query = `query($owner:String!,$name:String!){repository(owner:$owner,name:$name){id discussionCategories(first:25){nodes{id name}}}}`;
const response = JSON.parse(execFileSync('gh', ['api', 'graphql', '-f', `query=${query}`, '-F', `owner=${owner}`, '-F', `name=${name}`], { encoding: 'utf8' }));
const repository = response.data?.repository;
const category = repository?.discussionCategories?.nodes?.find((item) => item.name === 'General') || repository?.discussionCategories?.nodes?.[0];
if (!repository?.id || !category?.id) {
  console.error('无法读取仓库或讨论分类，请确认已开启 Discussions。');
  process.exit(1);
}
const configPath = path.join(process.cwd(), 'src/config/site.ts');
let source = fs.readFileSync(configPath, 'utf8');
source = source.replace(/repoId: '[^']*'/, `repoId: '${repository.id}'`).replace(/category: '[^']*'/, `category: '${category.name}'`).replace(/categoryId: '[^']*'/, `categoryId: '${category.id}'`);
fs.writeFileSync(configPath, source);
console.log(`Giscus 已配置：${category.name}`);
