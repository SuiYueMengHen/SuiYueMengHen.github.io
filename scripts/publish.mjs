import { spawnSync } from 'node:child_process';
const message = process.argv.slice(2).join(' ').trim();
if (!message) { console.error('用法：npm run publish -- "提交说明"'); process.exit(1); }
for (const [command,args] of [['npm',['run','check']],['npm',['run','test']],['npm',['run','build']],['git',['add','.']],['git',['commit','-m',message]],['git',['push','origin','main']]]) {
  const result=spawnSync(command,args,{stdio:'inherit'}); if(result.status!==0) process.exit(result.status??1);
}
console.log('已推送。GitHub Actions 正在发布网站。');
