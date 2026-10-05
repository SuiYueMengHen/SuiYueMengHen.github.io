import katex from 'katex';

/** Shared server-only renderer for Markdown and table-of-contents math. */
export function renderMath(source, displayMode = false, macros = {}) {
  return katex.renderToString(source, {
    displayMode,
    output: 'htmlAndMathml',
    throwOnError: true,
    strict: 'ignore',
    trust: false,
    maxExpand: 1000,
    macros,
  });
}

export function inlineMathSource(value) {
  return value.startsWith('\\(') && value.endsWith('\\)')
    ? value.slice(2, -2)
    : value;
}
