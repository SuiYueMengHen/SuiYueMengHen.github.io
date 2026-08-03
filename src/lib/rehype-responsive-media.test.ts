import {describe,expect,it} from 'vitest';
import {rehypeResponsiveMedia,responsiveMediaInternals} from './rehype-responsive-media.mjs';

const image=(name:string)=>({type:'element',tagName:'img',properties:{src:`./${name}`,alt:name},children:[]});
const paragraph=(children:any[])=>({type:'element',tagName:'p',properties:{'data-source-start':'3'},children});

describe('responsive article media',()=>{
  it('parses clamped widths and optional quoted captions',()=>{
    expect(responsiveMediaInternals.mediaOptions('{width=64% caption="一张图"} rest'))
      .toMatchObject({width:64,caption:'一张图'});
    expect(responsiveMediaInternals.mediaOptions('{width=64% caption=“智能引号”}'))
      .toMatchObject({width:64,caption:'智能引号'});
    expect(responsiveMediaInternals.mediaOptions('{width=180%}')).toMatchObject({width:100,caption:''});
  });

  it('turns one image into an accessible responsive figure',()=>{
    const tree:any={type:'root',children:[paragraph([image('a.webp'),{type:'text',value:'{width=72% caption="图注"}'}])]};
    rehypeResponsiveMedia()(tree);const figure=tree.children[0];
    expect(figure.tagName).toBe('figure');expect(figure.properties.style).toBe('--media-width:72%');
    expect(figure.children[0].properties).toMatchObject({loading:'lazy',decoding:'async'});
    expect(figure.children[1].children[0].value).toBe('图注');
  });

  it('supports the Markdown-and-MDX-safe Prism image title protocol',()=>{
    const titled:any=image('safe.webp');titled.properties.title='prism:width=58%;caption=兼容图注';
    const tree:any={type:'root',children:[paragraph([titled])]};rehypeResponsiveMedia()(tree);
    expect(tree.children[0].properties.style).toBe('--media-width:58%');expect(tree.children[0].children[1].children[0].value).toBe('兼容图注');expect(titled.properties.title).toBeUndefined();
  });

  it('groups fenced images while preserving independent widths',()=>{
    const tree:any={type:'root',children:[paragraph([{type:'text',value:':::gallery'}]),paragraph([image('a.webp'),{type:'text',value:'{width=40%}'}]),paragraph([image('b.webp'),{type:'text',value:'{width=60%}'}]),paragraph([{type:'text',value:':::'}])]};
    rehypeResponsiveMedia()(tree);expect(tree.children).toHaveLength(1);expect(tree.children[0].properties.className).toContain('media-gallery');
    expect(tree.children[0].children.map((item:any)=>item.properties.style)).toEqual(['--media-width:40%','--media-width:60%']);
  });
});
