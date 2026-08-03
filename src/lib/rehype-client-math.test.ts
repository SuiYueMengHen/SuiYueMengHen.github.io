import {describe,expect,it} from 'vitest';
import {rehypeClientMath} from './rehype-client-math.mjs';

describe('responsive client math source',()=>{
  it('converts display math to live TeX without a pre/code frame',()=>{
    const code:any={type:'element',tagName:'code',properties:{className:['language-math','math-display']},children:[{type:'text',value:'a+b=c \\tag{1}'}]};
    const tree:any={type:'root',children:[{type:'element',tagName:'pre',properties:{'data-source-start':'4'},children:[code]}]};
    rehypeClientMath()(tree);const math=tree.children[0];
    expect(math.tagName).toBe('div');expect(math.properties.className).toContain('math-source--display');expect(math.properties['data-source-start']).toBe('4');expect(math.children[0].value).toBe('\\[a+b=c \\tag{1}\\]');
  });
  it('converts inline math to browser-breakable TeX',()=>{
    const math:any={type:'element',tagName:'code',properties:{className:['math-inline']},children:[{type:'text',value:'x+y'}]};const tree:any={type:'root',children:[math]};
    rehypeClientMath()(tree);expect(tree.children[0].tagName).toBe('span');expect(tree.children[0].children[0].value).toBe('\\(x+y\\)');
  });
});
