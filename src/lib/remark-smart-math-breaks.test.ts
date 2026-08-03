import {describe,expect,it} from 'vitest';
import {smartBreakMath} from './remark-smart-math-breaks.mjs';

describe('smart display-math wrapping',()=>{
  it('breaks a long top-level expression without splitting fraction groups',()=>{
    const source='a_1+a_2+a_3+a_4+a_5+a_6+a_7+a_8+a_9+a_{10}+a_{11}+a_{12}+a_{13}+a_{14}+a_{15}+a_{16}+a_{17}+a_{18}';
    const result=smartBreakMath(source,34);expect(result).toContain('\\begin{aligned}');expect(result).toContain('\\\\');expect(result).toContain('a_{18}');
  });
  it('leaves authored multiline environments untouched',()=>{
    const source='\\begin{aligned} a &= b \\\\ c &= d \\end{aligned}';expect(smartBreakMath(source)).toBe(source);
  });
  it('keeps equation tags outside the generated aligned environment',()=>{
    const source='\\frac{\\alpha+i\\beta}{\\gamma+i\\delta}=\\frac{\\alpha\\gamma+\\beta\\delta}{\\gamma^2+\\delta^2}+i\\frac{\\beta\\gamma-\\alpha\\delta}{\\gamma^2+\\delta^2} \\tag{3}';
    const result=smartBreakMath(source);expect(result).toContain('\\begin{aligned}');expect(result).toMatch(/\\end\{aligned\}\\tag\{3\}$/);expect(result.match(/\\tag/g)).toHaveLength(1);
  });
  it('breaks at top-level TeX relation commands on every viewport',()=>{
    const source='\\left|\\sum_{i=1}^n a_i b_i\\right|^2 \\leqslant \\sum_{i=1}^n |a_i|^2 \\sum_{i=1}^n |b_i|^2 \\tag{14}';
    const result=smartBreakMath(source);expect(result).toContain('\\\\\n&{}\\leqslant');expect(result).toMatch(/\\tag\{14\}$/);
  });
});
