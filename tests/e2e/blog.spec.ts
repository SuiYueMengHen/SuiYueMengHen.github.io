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

test('移动端菜单可以打开', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile', '仅移动端');
  await page.goto('/');
  await page.getByRole('button', { name: '打开菜单' }).click();
  await expect(page.getByRole('navigation', { name: '主导航' })).toBeVisible();
});
