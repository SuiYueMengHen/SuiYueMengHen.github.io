import {describe,expect,it} from 'vitest';
import {rehypeEquationTags} from './rehype-equation-tags.mjs';

describe('equation tag layout',()=>{
  it('moves a trailing tag into a dedicated accessible column',()=>{
    const math:any={type:'element',tagName:'code',properties:{className:['math-display'],'data-source-start':'8'},children:[{type:'text',value:'a=b \\tag{12}'}]};const tree:any={type:'root',children:[math]};rehypeEquationTags()(tree);const shell=tree.children[0];
    expect(shell.properties.className).toEqual(['equation-shell']);expect(shell.children[0].children[0].value).toBe('a=b');expect(shell.children[1].children[0].value).toBe('(12)');expect(shell.children[1].properties['aria-label']).toBe('公式编号 12');
  });
  it('leaves unnumbered display math unchanged',()=>{
    const math:any={type:'element',tagName:'code',properties:{className:['math-display']},children:[{type:'text',value:'a=b'}]};const tree:any={type:'root',children:[math]};rehypeEquationTags()(tree);expect(tree.children[0]).toBe(math);
  });
});
