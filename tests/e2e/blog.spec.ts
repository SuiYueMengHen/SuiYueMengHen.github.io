import { expect, test } from '@playwright/test';

const article = '/blog/qm-notes-1-sets-relations-functions/';

test.beforeEach(async ({ page }) => {
  // Keep browser tests independent of the third-party Discussions service.
  await page.route('https://giscus.app/**', (route) => route.abort());
});

test('Home is minimal and About Me uses the real avatar, education timeline and selected project links', async ({
  page,
}) => {
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'SuiYueMengHen', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('img', { name: 'SuiYueMengHen 的 GitHub 头像' }),
  ).toBeVisible();
  await expect(page.locator('.project-card')).toHaveCount(0);
  await expect(page.locator('#site-nav a')).toHaveText([
    'Home',
    'Blog',
    'Projects',
    'About Me',
  ]);
  const menu = page.getByRole('button', { name: '打开菜单' });
  if (await menu.isVisible()) await menu.click();
  await page
    .locator('#site-nav')
    .getByRole('link', { name: 'About Me', exact: true })
    .click();
  await expect(page).toHaveURL(/\/about\/$/);
  await expect(
    page.getByRole('heading', {
      name: 'Wuhan University (School of Physics and Technology)',
    }),
  ).toBeVisible();
  await expect(page.locator('.timeline')).toContainText('2026—现在');
  await expect(page.locator('.research-interests li')).toHaveText([
    '量子光学',
    '非厄米物理',
  ]);
  await expect(page.locator('.project-card')).toHaveCount(2);
  await expect(
    page
      .locator('.project-card')
      .getByRole('link', { name: 'arxiv-physics', exact: true }),
  ).toHaveAttribute('href', 'https://github.com/SuiYueMengHen/arxiv-physics');
  for (const label of ['Home', 'Blog', 'Projects', 'About Me'])
    await expect(page.locator('#site-nav a', { hasText: label })).toHaveCount(
      1,
    );
});

test('theme follows the system, persists across routes and reloads, and supports reduced motion', async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
  await page.goto('/');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(page.locator('html')).toHaveCSS('scroll-behavior', 'auto');
  await page.getByRole('button', { name: '切换明暗主题' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  expect(await page.evaluate(() => localStorage.getItem('prism-theme'))).toBe(
    'light',
  );
  await page.goto('/blog/');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute(
    'content',
    '#ffffff',
  );
});

test('blog lists only the two published notes', async ({ page }) => {
  await page.goto('/blog/');
  await expect(page.locator('.post-card')).toHaveCount(2);
  await expect(page.locator('.post-card h2')).toContainText([
    '量子力学笔记（一）',
    '量子力学笔记（二）',
  ]);
  await expect(
    page.getByRole('link', { name: 'Markdown 阅读示例' }),
  ).toHaveCount(0);
});

test('project filtering works without removing home-page recommendations', async ({
  page,
}) => {
  await page.goto('/projects/');
  await expect(page.locator('.project-card')).toHaveCount(6);
  await page.getByRole('button', { name: 'TeX', exact: true }).click();
  await expect(page.locator('.project-item:visible')).toHaveCount(1);
  await expect(page.locator('.project-item:visible')).toContainText([
    'cntextbook',
  ]);
  await page.getByRole('button', { name: '全部', exact: true }).click();
  await expect(page.locator('.project-item:visible')).toHaveCount(6);
});

test('production full-text search finds existing article content', async ({
  page,
}) => {
  await page.goto('/search/?q=笛卡儿积');
  await expect(page.locator('#search-results h2').first()).toContainText(
    '量子力学笔记（一）',
  );
  await expect(page.locator('#search-status')).toContainText('找到');
  await page.getByRole('searchbox').fill('zznonexistentzzz');
  await expect(page.locator('#search-status')).toContainText('没有找到');
});

test('new blog routes are responsive while removed content is absent', async ({
  page,
}) => {
  const routes = [
    '/',
    '/about/',
    '/blog/',
    '/projects/',
    '/archive/',
    '/tags/',
    '/tags/数学基础/',
    '/search/',
    article,
    '/404.html',
  ];
  for (const width of [375, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of routes) {
      const response = await page.goto(route);
      expect(response?.status(), route).toBe(200);
      expect(
        await page.evaluate(
          () =>
            document.documentElement.scrollWidth <=
            document.documentElement.clientWidth,
        ),
        `${width}: ${route}`,
      ).toBe(true);
    }
  }
});

test('old blogs and classification routes are removed from the production output', async () => {
  const { existsSync } = await import('node:fs');
  for (const path of [
    'blog/example',
    'tags/Markdown',
    'blog/复数',
    'blog/矩阵与方程组',
    'blog/函数用无穷级数和无穷乘积展开',
    'categories',
    'collections',
  ])
    expect(existsSync(`dist/${path}`), path).toBe(false);
});

test('mobile navigation can be opened, closed with Escape and followed', async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile', 'Only mobile menu');
  await page.goto('/');
  await page.getByRole('button', { name: '打开菜单' }).click();
  await expect(page.getByRole('navigation', { name: '主导航' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: '打开菜单' })).toHaveAttribute(
    'aria-expanded',
    'false',
  );
  await page.getByRole('button', { name: '打开菜单' }).click();
  await page
    .getByRole('navigation', { name: '主导航' })
    .getByRole('link', { name: 'Blog', exact: true })
    .click();
  await expect(page).toHaveURL(/\/blog\/$/);
});

for (const slug of [
  'qm-notes-1-sets-relations-functions',
  'qm-notes-2-algebraic-structures',
]) {
  test(`published quantum note ${slug} renders formulas and text without JavaScript`, async ({
    browser,
  }) => {
    const context = await browser.newContext({
      javaScriptEnabled: false,
      viewport: { width: 375, height: 812 },
    });
    const page = await context.newPage();
    await page.goto(`/blog/${slug}/`);
    await expect(page.locator('.article-head h1')).toContainText(
      '量子力学笔记',
    );
    expect(await page.locator('.prose .katex').count()).toBeGreaterThan(20);
    await expect(page.locator('.katex-error')).toHaveCount(0);
    await expect(page.locator('.prose')).toContainText(
      slug.includes('notes-1') ? '延拓' : '域同态',
    );
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth <=
          document.documentElement.clientWidth,
      ),
    ).toBe(true);
    await context.close();
  });
}
