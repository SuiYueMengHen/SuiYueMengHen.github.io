import { fromHtml } from 'hast-util-from-html';
import { rehypeHeadingIds } from '@astrojs/markdown-remark';
import { renderMath } from './math.mjs';

function classes(node) {
  const value = node?.properties?.className;
  return Array.isArray(value) ? value : String(value || '').split(/\s+/);
}
function isMath(node, kind) {
  return node?.type === 'element' && classes(node).includes(`math-${kind}`);
}
function sourceText(node) {
  return (node.children || [])
    .filter((child) => child.type === 'text')
    .map((child) => child.value)
    .join('');
}

/** Pre-render formulas while retaining source markers for Prism Studio. */
export function rehypeStaticMath() {
  return (tree, file) => {
    // Astro collects headings after rehype plugins. Capture the original TeX
    // first, so visual HTML + accessible MathML are not counted three times.
    const sourceTree = structuredClone(tree);
    function preserveHeadingMath(node) {
      if (isMath(node, 'inline')) {
        node.children = [{ type: 'text', value: `\\(${sourceText(node)}\\)` }];
      } else {
        for (const child of node.children || []) preserveHeadingMath(child);
      }
    }
    preserveHeadingMath(sourceTree);
    const headingFile = {
      data: { astro: { frontmatter: file?.data?.astro?.frontmatter || {} } },
      history: file?.history || [],
    };
    rehypeHeadingIds()(sourceTree, headingFile);
    const sourceHeadings = headingFile.data.astro.headings;
    if (file) {
      file.data.astro ||= {};
      file.data.astro.frontmatter ||= {};
      file.data.astro.frontmatter.__mathHeadingSources = sourceHeadings;
    }
    let headingIndex = 0;
    function preserveIds(node) {
      if (node.type === 'element' && /^h[1-6]$/.test(node.tagName)) {
        node.properties ||= {};
        node.properties.id = sourceHeadings[headingIndex++]?.slug;
      }
      for (const child of node.children || []) preserveIds(child);
    }
    preserveIds(tree);
    // Macro state is shared within one article, never across articles.
    const macros = {};
    function walk(parent) {
      if (!Array.isArray(parent?.children)) return;
      parent.children = parent.children.map((node) => {
        const display =
          node?.type === 'element' && node.tagName === 'pre'
            ? node.children?.find((child) => isMath(child, 'display'))
            : undefined;
        const inline = isMath(node, 'inline');
        if (display || inline) {
          const math = display || node;
          let html;
          try {
            html = renderMath(sourceText(math), Boolean(display), macros);
          } catch (error) {
            if (file?.fail)
              file.fail(
                `Invalid formula: ${error.message}`,
                math.position || node.position,
              );
            throw error;
          }
          return {
            type: 'element',
            tagName: display ? 'div' : 'span',
            position: node.position,
            properties: {
              ...node.properties,
              'data-pagefind-ignore': '',
              className: [
                'math-source',
                display ? 'math-source--display' : 'math-source--inline',
              ],
            },
            children: fromHtml(html, { fragment: true }).children,
          };
        }
        walk(node);
        return node;
      });
    }
    walk(tree);
  };
}
