import {describe,expect,it} from 'vitest';
import {rehypeAttachEquationTags,rehypeExtractEquationTags} from './rehype-equation-tags.mjs';

describe('equation tag layout',()=>{
  it('keeps MathJax pre/code structure intact until rendering, then attaches an accessible tag',()=>{
    const math:any={type:'element',tagName:'code',properties:{className:['math-display'],'data-source-start':'8'},children:[{type:'text',value:'a=b \\tag{12}'}]};
    const pre:any={type:'element',tagName:'pre',properties:{},children:[math]};const tree:any={type:'root',children:[pre]};
    rehypeExtractEquationTags()(tree);
    expect(tree.children[0]).toBe(pre);expect(math.children[0].value).toBe('a=b');expect(tree.children[1].properties.dataEquationTag).toBe('12');
    tree.children[0]={type:'element',tagName:'mjx-container',properties:{display:'true'},children:[]};
    rehypeAttachEquationTags()(tree);const shell=tree.children[0];
    expect(shell.properties.className).toEqual(['equation-shell']);expect(shell.children[1].children[0].value).toBe('(12)');expect(shell.children[1].properties['aria-label']).toBe('公式编号 12');
  });
  it('leaves unnumbered display math unchanged',()=>{
    const math:any={type:'element',tagName:'code',properties:{className:['math-display']},children:[{type:'text',value:'a=b'}]};const tree:any={type:'root',children:[{type:'element',tagName:'pre',properties:{},children:[math]}]};
    rehypeExtractEquationTags()(tree);expect(tree.children).toHaveLength(1);expect(tree.children[0].children[0]).toBe(math);
  });
});
