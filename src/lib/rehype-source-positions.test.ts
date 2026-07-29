import { describe, expect, it } from 'vitest';
import { rehypeSourcePositions } from './rehype-source-positions.mjs';

describe('rehypeSourcePositions', () => {
  it('adds source ranges only to positioned rendered elements', () => {
    const tree = {
      type: 'root',
      children: [
        { type: 'element', tagName: 'h2', properties: {}, position: { start: { line: 4 }, end: { line: 4 } }, children: [] },
        { type: 'element', tagName: 'p', properties: {}, position: { start: { line: 6 }, end: { line: 8 } }, children: [] },
        { type: 'element', tagName: 'span', properties: {}, children: [] },
      ],
    };
    rehypeSourcePositions()(tree);
    expect(tree.children[0].properties).toMatchObject({ 'data-source-start': '4', 'data-source-end': '4' });
    expect(tree.children[1].properties).toMatchObject({ 'data-source-start': '6', 'data-source-end': '8' });
    expect(tree.children[2].properties).toEqual({});
  });
});
