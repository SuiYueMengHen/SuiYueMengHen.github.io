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

export function articleDisplaySettings(data: ArticleDisplaySource) {
  return {
    autoNumbering: data.autoNumbering ?? true,
    showContents: data.showContents ?? true,
    showSideToc: data.showSideToc ?? true,
  };
}

export function articleTocHeadings(headings: ArticleHeading[], autoNumbering = true) {
  let chapter = 0;
  let section = 0;
  let subsection = 0;

  return headings.filter(({ depth }) => depth >= 2 && depth <= 4).map((heading) => {
    if (heading.depth === 2) {
      chapter += 1;
      section = 0;
      subsection = 0;
    } else if (heading.depth === 3) {
      section += 1;
      subsection = 0;
    } else {
      subsection += 1;
    }
    const number = !autoNumbering ? '' : heading.depth === 2
      ? `第${chapter}章`
      : heading.depth === 3
        ? `§${chapter}.${section}`
        : `§${chapter}.${section}.${subsection}`;
    return { ...heading, number };
  });
}
