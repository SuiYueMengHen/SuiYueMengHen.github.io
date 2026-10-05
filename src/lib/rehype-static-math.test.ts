import { describe, expect, it } from 'vitest';
import { createMarkdownProcessor } from '@astrojs/markdown-remark';
import remarkMath from 'remark-math';
import { rehypeStaticMath } from './rehype-static-math.mjs';
import { renderMath, inlineMathSource } from './math.mjs';

const code = (source: string, kind = 'inline'): any => ({
  type: 'element',
  tagName: 'code',
  properties: { className: ['language-math', `math-${kind}`] },
  children: [{ type: 'text', value: source }],
});
const json = (node: unknown) => JSON.stringify(node);

describe('build-time formula rendering', () => {
  it('renders accessible inline and numbered display math without browser JavaScript', () => {
    const tree: any = {
      type: 'root',
      children: [
        code('E=mc^2'),
        {
          type: 'element',
          tagName: 'pre',
          properties: { 'data-source-start': '7' },
          children: [
            code(String.raw`\int_0^1 x^2\,dx = \frac{1}{3} \tag{1}`, 'display'),
          ],
        },
      ],
    };
    rehypeStaticMath()(tree);
    expect(tree.children[0].tagName).toBe('span');
    expect(tree.children[1].tagName).toBe('div');
    expect(tree.children[1].properties['data-source-start']).toBe('7');
    expect(json(tree)).toContain('katex');
    expect(json(tree)).toContain('MathML');
    expect(json(tree)).toContain('annotation');
    expect(json(tree)).not.toContain('mjx-container');
  });

  it('keeps article macro definitions local and leaves ordinary code untouched', () => {
    const normal = {
      type: 'element',
      tagName: 'code',
      properties: {},
      children: [{ type: 'text', value: 'const x = 1' }],
    };
    const tree: any = {
      type: 'root',
      children: [
        code(String.raw`\gdef\RR{\mathbb{R}}`),
        code(String.raw`x\in\RR`),
        normal,
      ],
    };
    rehypeStaticMath()(tree);
    expect(tree.children[2]).toBe(normal);
    expect(() =>
      rehypeStaticMath()({ type: 'root', children: [code(String.raw`\RR`)] }),
    ).toThrow();
  });

  it('fails invalid TeX at build time instead of silently publishing a broken formula', () => {
    expect(() =>
      rehypeStaticMath()({
        type: 'root',
        children: [code(String.raw`\frac{`)],
      }),
    ).toThrow();
  });

  it('renders directory math with the same server renderer and blocks active HTML commands', () => {
    const html = renderMath(inlineMathSource(String.raw`\(P_\lambda(t)\)`));
    expect(html).toContain('katex-mathml');
    expect(html).toContain('P_\\lambda(t)');
    expect(renderMath(String.raw`\href{javascript:alert(1)}{x}`)).not.toContain(
      'href="javascript:',
    );
  });
});

it('keeps heading TeX and stable anchor ids through the actual Astro Markdown pipeline', async () => {
  const processor = await createMarkdownProcessor({
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeStaticMath],
    syntaxHighlight: false,
  });
  const result = await processor.render(
    String.raw`## 周期函数 $P_\lambda(t)$ 的展开`,
  );
  const sources = result.metadata.frontmatter.__mathHeadingSources;
  expect(sources).toHaveLength(1);
  expect(sources[0].text).toBe(String.raw`周期函数 \(P_\lambda(t)\) 的展开`);
  expect(result.metadata.headings[0].slug).toBe(sources[0].slug);
  expect(result.code).toContain('katex-mathml');
});
