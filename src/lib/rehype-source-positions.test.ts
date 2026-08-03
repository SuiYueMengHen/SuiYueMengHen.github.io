import { describe, expect, it } from 'vitest';
import { rehypeSourcePositions } from './rehype-source-positions.mjs';

const heading=(depth:number,line:number):any=>({type:'element',tagName:`h${depth}`,properties:{},children:[],position:{start:{line},end:{line}}});

describe('rehype heading metadata',()=>{
  it('writes the same numbering used by the article TOCs',()=>{
    const children=[heading(1,1),heading(2,2),heading(3,3),heading(6,4)];
    const tree={type:'root',children};rehypeSourcePositions()(tree);
    expect(children.map(node=>node.properties['data-heading-number']))
      .toEqual(['一、','§1.1','§1.1.1','§1.1.1.1.1.1']);
    expect(children[0].properties['data-source-start']).toBe('1');
  });

  it('uses an implicit first section when Markdown begins at ##',()=>{
    const children=[heading(2,1),heading(3,2)];rehypeSourcePositions()({type:'root',children});
    expect(children.map(node=>node.properties['data-heading-number'])).toEqual(['§1.1','§1.1.1']);
  });
});
