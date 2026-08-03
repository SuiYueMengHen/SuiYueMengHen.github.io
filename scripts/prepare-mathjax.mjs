import { cp, copyFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const root=resolve(import.meta.dirname,'..');
const packageRoot=resolve(root,'node_modules/mathjax');
const fontRoot=resolve(root,'node_modules/@mathjax/mathjax-newcm-font/svg/dynamic');
const outputRoot=resolve(root,'public/vendor/mathjax');
const outputFont=resolve(outputRoot,'fonts/mathjax-newcm-font/svg/dynamic');

await mkdir(outputFont,{recursive:true});
await copyFile(resolve(packageRoot,'tex-svg.js'),resolve(outputRoot,'tex-svg.js'));
await cp(fontRoot,outputFont,{recursive:true,force:true});
await cp(resolve(packageRoot,'sre'),resolve(outputRoot,'sre'),{recursive:true,force:true});
console.log('✓ MathJax 4 响应式渲染资源已准备');
