import { expect, test } from '@playwright/test';

test('首页提供科技感三维 Hero 与完整主导航', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /把复杂世界/ })).toBeVisible();
  await expect(page.getByRole('img', { name: /三维棱镜/ })).toBeVisible();
  await expect(page.locator('[data-prism-stage]')).toHaveCount(1);
  await expect(page.getByRole('link', { name: '进入合集' })).toBeVisible();
  await expect(page.getByRole('link', { name: /浏览归档/ })).toBeVisible();
  for (const label of ['首页', '合集', '分类', '归档', '项目', '关于']) {
    await expect(page.locator('#site-nav a', { hasText: label })).toHaveCount(1);
  }
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute('href', '/favicon.png');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
});

test('主题切换持久化且减少动态效果时 Hero 静止', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await expect.poll(() => page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior)).toBe('auto');
  await expect.poll(() => page.locator('[data-prism-stage]').evaluate((element) => getComputedStyle(element).transform)).toBe('none');
  await page.getByRole('button', { name: '切换明暗主题' }).click();
  await expect.poll(() => page.evaluate(() => localStorage.getItem('prism-theme'))).toMatch(/light|dark/);
});

test('暗色模式代码块使用独立高对比度配色', async ({ page }) => {
  await page.goto('/blog/markdown%E5%85%A5%E9%97%A8%E6%95%99%E7%A8%8B/');
  await page.evaluate(() => { document.documentElement.dataset.theme = 'dark'; });
  const block = page.locator('.astro-code').first();
  await expect(block).toBeVisible();
  const colors = await block.evaluate((element) => {
    const token = element.querySelector<HTMLElement>('span[style*="--shiki-dark"]');
    return {
      background: getComputedStyle(element).backgroundColor,
      foreground: token ? getComputedStyle(token).color : '',
    };
  });
  expect(colors.background).toBe('rgb(13, 17, 23)');
  expect(colors.foreground).not.toBe('rgb(24, 24, 22)');
});

test('文章不再段首缩进且标准 Markdown 软换行保持同段', async ({ page }) => {
  await page.goto('/blog/markdown%E5%85%A5%E9%97%A8%E6%95%99%E7%A8%8B/');
  const indent = await page.locator('.prose > p').first().evaluate((element) => getComputedStyle(element).textIndent);
  expect(indent).toBe('0px');
  await page.getByRole('button', { name: '打开阅读设置' }).click();
  await expect(page.getByRole('dialog', { name: '阅读设置' })).toBeVisible();
  await expect(page.locator('#paragraph-indent')).toHaveCount(0);
  await page.locator('#font-size').fill('20');
  await expect.poll(() => page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--reader-font-size').trim())).toBe('20px');
  await expect.poll(() => page.evaluate(() => localStorage.getItem('prism-reader-settings'))).not.toContain('paragraphIndent');
});

test('文章页保留目录、统计、代码复制与 MathJax', async ({ page }, testInfo) => {
  await page.goto('/blog/markdown%E5%85%A5%E9%97%A8%E6%95%99%E7%A8%8B/');
  await expect(page.getByRole('navigation', { name: '文章目录' })).toContainText('第1章');
  await expect(page.getByRole('button', { name: '复制代码' }).first()).toBeVisible();
  await expect(page.locator('.byline')).toContainText(/\d+ 字/);
  await expect(page.locator('.byline')).toContainText(/约 \d+ 分钟阅读/);
  if (testInfo.project.name === 'desktop') await expect(page.getByRole('navigation', { name: '随文目录' })).toBeVisible();
  await page.goto('/blog/maxwell%E6%96%B9%E7%A8%8B%E7%BB%84/');
  await expect(page.locator('mjx-container[jax="SVG"][display="true"]')).toHaveCount(3);
  await expect(page.locator('.mathjax-error')).toHaveCount(0);
});

test('归档页面恢复并按年份列出文章', async ({ page }) => {
  await page.goto('/archive/');
  await expect(page.getByRole('heading', { name: '归档' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '2026' })).toBeVisible();
  await expect(page.getByRole('link', { name: /markdown入门教程/ })).toBeVisible();
  await expect(page.getByRole('link', { name: /Maxwell方程组/ })).toBeVisible();
});

test('合集、分类、项目和关于页保持可用', async ({ page }, testInfo) => {
  await page.goto('/blog/');
  await expect(page.getByRole('heading', { name: '合集书架' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'C++从零到无穷大' })).toBeVisible();
  await page.goto('/categories/');
  await expect(page.getByRole('heading', { name: '分类目录' })).toBeVisible();
  await expect(page.getByRole('link', { name: /markdown入门教程/ }).first()).toBeVisible();
  if (testInfo.project.name === 'desktop') await expect(page.getByText('快速索引')).toBeVisible();
  else await expect(page.locator('#category-jump')).toBeVisible();
  await page.goto('/projects/');
  await expect(page.getByRole('heading', { name: '项目', exact: true })).toBeVisible();
  await page.goto('/about/');
  await expect(page.getByRole('heading', { name: /慢一点思考/ })).toBeVisible();
});

test('移动端菜单可以打开', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile', '仅移动端');
  await page.goto('/');
  await page.getByRole('button', { name: '打开菜单' }).click();
  await expect(page.getByRole('navigation', { name: '主导航' })).toBeVisible();
});

test('滚动保持原生且关键断点无横向溢出', async ({ page }) => {
  for (const width of [375, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ['/', '/archive/', '/blog/', '/categories/', '/projects/', '/about/']) {
      await page.goto(route);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
    }
  }
  await page.goto('/');
  const prevented = await page.evaluate(() => {
    const event = new WheelEvent('wheel', { deltaY: 100, cancelable: true });
    window.dispatchEvent(event);
    return event.defaultPrevented;
  });
  expect(prevented).toBe(false);
});
