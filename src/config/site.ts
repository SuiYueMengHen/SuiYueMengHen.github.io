export const siteConfig = {
  name: '棱镜笔记',
  englishName: 'Prism Notes',
  description: '记录技术、创造与日常观察，把复杂世界折射成清晰的文字。',
  site: 'https://suiyuemenghen.github.io',
  locale: 'zh-CN',
  author: {
    name: 'SuiYueMengHen',
    bio: '记录技术、创造与日常观察。',
    github: 'https://github.com/SuiYueMengHen',
  },
  hero: {
    eyebrow: 'A personal journal of technology, creation & observation',
    title: '把复杂世界，\n折射成清晰的文字。',
    introduction: '关于技术、创造与日常观察的个人写作空间。慢一点思考，认真地记录。',
  },
  nav: [
    { label: '文章', href: '/blog/' },
    { label: '分类', href: '/categories/' },
    { label: '归档', href: '/archive/' },
    { label: '关于', href: '/about/' },
  ],
  postsPerPage: 9,
  reading: {
    fontSize: 17,
    lineHeight: 1.85,
    contentWidth: 46,
    paragraphIndent: true,
    smoothScroll: true,
  },
  comments: {
    enabled: true,
    repo: 'SuiYueMengHen/SuiYueMengHen.github.io',
    repoId: 'R_kgDOTl6_uw',
    category: 'General',
    categoryId: 'DIC_kwDOTl6_u84DCJhQ',
    themes: {
      light: 'https://cdn.jsdelivr.net/gh/SuiYueMengHen/SuiYueMengHen.github.io@main/public/giscus-latex-light.css',
      dark: 'https://cdn.jsdelivr.net/gh/SuiYueMengHen/SuiYueMengHen.github.io@main/public/giscus-latex-dark.css',
    },
  },
  analytics: { enabled: false, scriptUrl: '' },
} as const;

export type SiteConfig = typeof siteConfig;
