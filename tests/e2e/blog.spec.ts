import { expect, test } from '@playwright/test';

test('首页包含核心内容且没有横向溢出', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /把复杂世界/ })).toBeVisible();
  await expect(page.getByRole('link', { name: '开始阅读' })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
});

test('主题切换会持久化', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: '切换明暗主题' }).click();
  await expect.poll(() => page.evaluate(() => localStorage.getItem('prism-theme'))).toMatch(/light|dark/);
});

test('文章页提供目录与代码复制', async ({ page }) => {
  await page.goto('/blog/building-a-digital-garden/');
  await expect(page.getByRole('navigation', { name: '相邻文章' })).toBeVisible();
  await expect(page.getByRole('button', { name: '复制代码' })).toBeVisible();
});

test('书籍目录与章节编号支持快速跳转', async ({ page }, testInfo) => {
  await page.goto('/blog/designing-with-constraints/');
  const toc = page.getByRole('navigation', { name: '文章目录' });
  await expect(toc).toContainText('第1章');
  await expect(toc).toContainText('§1.1');
  await expect(toc).toContainText('§1.1.1');
  const sectionLink = toc.getByRole('link', { name: /§1\.1 字体角色/ });
  await sectionLink.click();
  await expect.poll(() => page.evaluate(() => decodeURIComponent(location.hash))).toBe('#字体角色');
  const indent = await page.locator('.prose > p').first().evaluate((element) => getComputedStyle(element).textIndent);
  expect(indent).not.toBe('0px');
  if (testInfo.project.name === 'desktop') {
    await expect(page.getByRole('navigation', { name: '随文目录' })).toBeVisible();
    await expect(page.locator('.side-toc a[aria-current]')).toHaveCount(1);
  }
});

test('阅读设置可以修改并保存排版偏好', async ({ page }) => {
  await page.goto('/blog/designing-with-constraints/');
  await page.getByRole('button', { name: '打开阅读设置' }).click();
  await expect(page.getByRole('dialog', { name: '阅读设置' })).toBeVisible();
  await page.locator('#font-size').fill('20');
  await expect.poll(() => page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--reader-font-size').trim())).toBe('20px');
  await expect.poll(() => page.evaluate(() => localStorage.getItem('prism-reader-settings'))).toContain('"fontSize":20');
  await page.getByRole('button', { name: '恢复默认' }).click();
  await page.getByRole('button', { name: '完成' }).click();
  await expect.poll(() => page.evaluate(() => document.documentElement.dataset.smoothScroll)).toBe('true');
});

test('LaTeX 公式同时输出可视公式与 MathML', async ({ page }) => {
  await page.goto('/blog/designing-with-constraints/');
  await expect(page.locator('.katex-display')).toHaveCount(1);
  await expect(page.locator('.katex math').first()).toBeAttached();
  const font = await page.locator('.prose').evaluate((element) => getComputedStyle(element).fontFamily);
  expect(font).toContain('Computer Modern Serif');
});

test('移动端菜单可以打开', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile', '仅移动端');
  await page.goto('/');
  await page.getByRole('button', { name: '打开菜单' }).click();
  await expect(page.getByRole('navigation', { name: '主导航' })).toBeVisible();
});
