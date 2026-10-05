export const siteConfig = {
  name: 'SuiYueMengHen',
  englishName: 'Personal Notes',
  description: '记录技术、创造与日常观察，把复杂世界折射成清晰的文字。',
  site: 'https://suiyuemenghen.github.io',
  locale: 'zh-CN',
  author: {
    name: 'SuiYueMengHen',
    bio: '记录技术、创造与日常观察。',
    avatar: '/images/github-avatar.png',
    tagline: '记录思考，构建有用的工具。',
    // 从早到晚填写真实履历；空数组时显示待补充状态。
    timeline: [{ period: '2026—现在', title: 'Wuhan University' }] as Array<{
      period: string;
      title: string;
      description?: string;
    }>,
    github: 'https://github.com/SuiYueMengHen',
    focus: ['软件与工具', '数字写作', '日常观察'],
    principles: [
      { title: '诚实', description: '只写真正经历、学习和思考过的事情。' },
      { title: '清晰', description: '不拿复杂冒充深刻，把推理过程交代完整。' },
      {
        title: '长期',
        description: '允许文章被修订、连接，并随理解一同生长。',
      },
    ],
  },
  nav: [
    { label: 'About Me', href: '/' },
    { label: 'Blog', href: '/blog/' },
    { label: 'Projects', href: '/projects/' },
  ],
  postsPerPage: 9,
  reading: {
    fontSize: 17,
    lineHeight: 1.85,
    contentWidth: 46,
  },
  comments: {
    enabled: true,
    repo: 'SuiYueMengHen/SuiYueMengHen.github.io',
    repoId: 'R_kgDOTl6_uw',
    category: 'General',
    categoryId: 'DIC_kwDOTl6_u84DCJhQ',
    themes: {
      light:
        'https://cdn.jsdelivr.net/gh/SuiYueMengHen/SuiYueMengHen.github.io@main/public/giscus-latex-light.css',
      dark: 'https://cdn.jsdelivr.net/gh/SuiYueMengHen/SuiYueMengHen.github.io@main/public/giscus-latex-dark.css',
    },
  },
  analytics: { enabled: false, scriptUrl: '' },
} as const;

export type SiteConfig = typeof siteConfig;
