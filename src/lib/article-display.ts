export type ArticleDisplaySource = {
  autoNumbering?: boolean;
  showContents?: boolean;
  showSideToc?: boolean;
};

export type ArticleHeading = {
  depth: number;
  slug: string;
  text: string;
};

export type TocTextPart = {
  kind: 'text' | 'math';
  value: string;
};

export function articleDisplaySettings(data: ArticleDisplaySource) {
  return {
    autoNumbering: data.autoNumbering ?? true,
    showContents: data.showContents ?? true,
    showSideToc: data.showSideToc ?? true,
  };
}

export function chineseSectionNumber(value: number) {
  if (!Number.isInteger(value) || value <= 0) return String(value);
  const digits = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
  if (value < 10) return digits[value];
  if (value < 20) return `十${value % 10 ? digits[value % 10] : ''}`;
  if (value < 100) return `${digits[Math.floor(value / 10)]}十${value % 10 ? digits[value % 10] : ''}`;
  return String(value);
}

export function articleTocHeadings(headings: ArticleHeading[], autoNumbering = true) {
  const counts = Array(7).fill(0) as number[];
  return headings.filter(({ depth }) => depth >= 1 && depth <= 6).map((heading) => {
    const depth=heading.depth;
    for(let level=1;level<depth;level+=1)if(counts[level]===0)counts[level]=1;
    counts[depth]+=1;
    for(let level=depth+1;level<=6;level+=1)counts[level]=0;
    const number = !autoNumbering ? '' : depth === 1
      ? `${chineseSectionNumber(counts[1])}、`
      : `§${counts.slice(1,depth+1).join('.')}`;
    return { ...heading, number };
  });
}

/**
 * Restore the inline-math wrapper that is lost when Astro exposes rendered
 * headings as plain text. Single-dollar TeX is inline; double-dollar TeX is
 * deliberately left alone because it is display math and invalid in a title.
 */
export function articleTocTextParts(text: string): TocTextPart[] {
  const parts: TocTextPart[] = [];
  const inlineMath = /\\\([\s\S]*?\\\)|(?<!\$)\$(?!\$)(?:\\.|[^$\\])+\$(?!\$)/g;
  let cursor = 0;

  for (const match of text.matchAll(inlineMath)) {
    const start = match.index ?? 0;
    if (start > cursor) parts.push({ kind: 'text', value: text.slice(cursor, start) });
    const source = match[0];
    parts.push({
      kind: 'math',
      value: source.startsWith('\\(') ? source : `\\(${source.slice(1, -1)}\\)`,
    });
    cursor = start + source.length;
  }

  if (cursor < text.length) parts.push({ kind: 'text', value: text.slice(cursor) });
  return parts.length ? parts : [{ kind: 'text', value: text }];
}
