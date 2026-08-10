import { describe, expect, it } from 'vitest';
import { articleDisplaySettings, articleTocHeadings, articleTocTextParts } from './article-display';

describe('article display settings', () => {
  it('keeps every reading aid enabled for legacy articles', () => {
    expect(articleDisplaySettings({})).toEqual({
      autoNumbering: true,
      showContents: true,
      showSideToc: true,
    });
  });

  it('allows every option to be switched independently', () => {
    expect(articleDisplaySettings({ autoNumbering: false, showContents: true, showSideToc: false }))
      .toEqual({ autoNumbering: false, showContents: true, showSideToc: false });
  });

  it('numbers Markdown heading levels from section through nested symbols', () => {
    const headings = [
      { depth: 1, slug: 'one', text: '一' },
      { depth: 2, slug: 'one-one', text: '一点一' },
      { depth: 3, slug: 'one-one-one', text: '一点一点一' },
      { depth: 4, slug: 'deep', text: '四级' },
      { depth: 5, slug: 'deeper', text: '五级' },
      { depth: 6, slug: 'deepest', text: '六级' },
    ];
    expect(articleTocHeadings(headings, true).map(({ number }) => number))
      .toEqual(['一、', '§1.1', '§1.1.1', '§1.1.1.1', '§1.1.1.1.1', '§1.1.1.1.1.1']);
    expect(articleTocHeadings(headings, false).map(({ text, number }) => [text, number]))
      .toEqual(headings.map(({ text }) => [text, '']));
  });

  it('creates implicit parent section numbers when an article starts at ##', () => {
    expect(articleTocHeadings([
      { depth:2,slug:'one-one',text:'一点一' },
      { depth:3,slug:'one-one-one',text:'一点一点一' },
    ],true).map(({number})=>number)).toEqual(['§1.1','§1.1.1']);
  });

  it('uses readable Chinese numerals for top-level sections', () => {
    const headings=Array.from({length:11},(_,index)=>({depth:1,slug:String(index),text:String(index)}));
    expect(articleTocHeadings(headings,true).map(({number})=>number))
      .toEqual(['一、','二、','三、','四、','五、','六、','七、','八、','九、','十、','十一、']);
  });

  it('keeps single-dollar heading math inline without treating display math as inline', () => {
    expect(articleTocTextParts('周期函数 $P_\lambda(t)$ 的展开')).toEqual([
      { kind: 'text', value: '周期函数 ' },
      { kind: 'math', value: '\\(P_\lambda(t)\\)' },
      { kind: 'text', value: ' 的展开' },
    ]);
    expect(articleTocTextParts('周期函数 \\(P_\lambda(t)\\) 的展开')[1])
      .toEqual({ kind: 'math', value: '\\(P_\lambda(t)\\)' });
    expect(articleTocTextParts('错误标题 $$P_\lambda(t)$$')).toEqual([
      { kind: 'text', value: '错误标题 $$P_\lambda(t)$$' },
    ]);
  });
});
