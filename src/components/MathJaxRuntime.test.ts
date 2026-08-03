import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const runtimeSource = readFileSync(new URL('./MathJaxRuntime.astro', import.meta.url), 'utf8');

describe('MathJax responsive layout contract', () => {
  it('keeps inline math atomic while display math uses the full live measure', () => {
    expect(runtimeSource).toContain("linebreaks:{inline:false,width:'100%'");
    expect(runtimeSource).toContain(".math-source--inline>mjx-container:not([display='true']){display:inline-block!important;width:auto!important");
  });

  it('centres the block SVG without scaling it down', () => {
    expect(runtimeSource).toContain(".math-source--display>mjx-container[display='true']>svg{position:relative;left:50%;margin-inline:0;transform:translateX(-50%)}");
    expect(runtimeSource).not.toContain('max-width:100%!important');
  });
});
