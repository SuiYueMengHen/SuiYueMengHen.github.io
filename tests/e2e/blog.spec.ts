import { expect, test } from '@playwright/test';

const article = '/blog/函数用无穷级数和无穷乘积展开/';

test.beforeEach(async ({ page }) => {
  // Keep browser tests independent of the third-party Discussions service.
  await page.route('https://giscus.app/**', (route) => route.abort());
});

test('About Me uses the real avatar, education timeline and selected project links', async ({
  page,
}) => {
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'SuiYueMengHen', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('img', { name: 'SuiYueMengHen 的 GitHub 头像' }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Wuhan University' }),
  ).toBeVisible();
  await expect(page.locator('.timeline')).toContainText('2026—现在');
  await expect(page.locator('.project-card')).toHaveCount(2);
  await expect(
    page
      .locator('.project-card')
      .getByRole('link', { name: 'arxiv-physics', exact: true }),
  ).toHaveAttribute('href', 'https://github.com/SuiYueMengHen/arxiv-physics');
  for (const label of ['About Me', 'Blog', 'Projects'])
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

test('blog supports pinned covers, chronology, filtering and an empty-result recovery', async ({
  page,
}) => {
  await page.goto('/blog/');
  await expect(
    page.getByRole('heading', { name: 'Blog', exact: true }),
  ).toBeVisible();
  await expect(page.locator('.pinned-grid .post-card')).toHaveCount(1);
  await expect(page.locator('.pinned-grid img')).toBeVisible();
  await expect(page.locator('[data-chronological]')).toHaveCount(3);
  await page.getByRole('searchbox').fill('矩阵');
  await expect(page.locator('[data-chronological]:visible')).toHaveCount(1);
  await expect(page.locator('.pinned-section')).toBeHidden();
  await page.getByRole('searchbox').fill('不存在的文章 xyz');
  await expect(
    page.getByRole('heading', { name: '没有匹配的文章' }),
  ).toBeVisible();
  await page.getByRole('button', { name: '清除筛选' }).click();
  await expect(page.locator('[data-chronological]:visible')).toHaveCount(3);
  await page.getByRole('button', { name: '待整理', exact: true }).click();
  await expect(
    page.getByRole('button', { name: '待整理', exact: true }),
  ).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('[data-chronological]:visible')).toHaveCount(3);
});

test('project filtering works without removing home-page recommendations', async ({
  page,
}) => {
  await page.goto('/projects/');
  await expect(page.locator('.project-card')).toHaveCount(10);
  await page.getByRole('button', { name: 'TeX', exact: true }).click();
  await expect(page.locator('.project-item:visible')).toHaveCount(2);
  await expect(page.locator('.project-item:visible')).toContainText([
    'GaokaoTeX',
    'cntextbook',
  ]);
  await page.getByRole('button', { name: '全部', exact: true }).click();
  await expect(page.locator('.project-item:visible')).toHaveCount(10);
});

test('formulas and directory math are rendered before JavaScript, with readable long equations', async ({
  browser,
}) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 375, height: 812 },
  });
  const page = await context.newPage();
  await page.goto(article);
  expect(await page.locator('.prose .katex').count()).toBeGreaterThan(50);
  await expect(page.locator('.prose .katex').first()).toBeVisible();
  await expect(page.locator('.book-toc')).not.toHaveAttribute('open');
  await page.locator('.book-toc summary').click();
  await expect(
    page.locator('.book-toc .toc-inline-math .katex').first(),
  ).toBeVisible();
  expect(await page.locator('.book-toc .toc-inline-math .katex').count()).toBe(
    2,
  );
  expect(await page.locator('.side-toc .toc-inline-math .katex').count()).toBe(
    2,
  );
  expect(await page.locator('.katex-error, mjx-container').count()).toBe(0);
  await expect(page.locator('script[src*="mathjax"]')).toHaveCount(0);
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
  expect(
    await page
      .locator('.prose blockquote')
      .first()
      .evaluate((node) => getComputedStyle(node).fontStyle),
  ).toBe('normal');
  await context.close();
});

test('reader preferences can be changed and survive an article reload', async ({
  page,
}) => {
  await page.goto(article);
  await page.getByRole('button', { name: '打开阅读设置' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('slider', { name: /正文字号/ }).fill('20');
  await page.getByRole('button', { name: '完成', exact: true }).click();
  await expect(page.locator('.prose')).toHaveCSS('font-size', '20px');
  await page.reload();
  await expect(page.locator('.prose')).toHaveCSS('font-size', '20px');
});

test('production full-text search finds existing article content', async ({
  page,
}) => {
  await page.goto('/search/?q=伯努利');
  await expect(page.locator('#search-results h2').first()).toContainText(
    '函数用无穷级数和无穷乘积展开',
  );
  await expect(page.locator('#search-status')).toContainText('找到');
  await page.getByRole('searchbox').fill('zznonexistentzzz');
  await expect(page.locator('#search-status')).toContainText('没有找到');
});

test('all existing index and article routes remain available without horizontal overflow', async ({
  page,
}) => {
  const routes = [
    '/',
    '/about/',
    '/blog/',
    '/projects/',
    '/archive/',
    '/categories/',
    '/categories/微积分/',
    '/tags/',
    '/tags/待整理/',
    '/collections/',
    '/collections/特殊函数概论/',
    '/search/',
    '/blog/复数/',
    '/blog/矩阵与方程组/',
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
