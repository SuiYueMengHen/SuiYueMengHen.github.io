import { expect, test } from '@playwright/test';

test('首页包含核心内容且没有横向溢出', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /把复杂世界/ })).toBeVisible();
  await expect(page.getByRole('link', { name: '开始阅读' })).toBeVisible();
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute('href', '/favicon.png');
  await expect(page.locator('.brand img[src="/prism-icon.png"]')).toHaveCount(1);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
  for (const label of ['首页', '合集', '分类', '项目', '关于']) await expect(page.locator('#site-nav a', { hasText: label })).toHaveCount(1);
});

test('主题切换会持久化', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: '切换明暗主题' }).click();
  await expect.poll(() => page.evaluate(() => localStorage.getItem('prism-theme'))).toMatch(/light|dark/);
  await expect.poll(() => page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--theme-radius').trim())).not.toBe('');
});

test('减少动态效果时主题与锚点即时切换',async({page})=>{await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/');await expect.poll(()=>page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior)).toBe('auto');await page.getByRole('button',{name:'切换明暗主题'}).click();await expect.poll(()=>page.evaluate(()=>localStorage.getItem('prism-theme'))).toMatch(/light|dark/)});

test('文章页提供目录与代码复制', async ({ page }) => {
  await page.goto('/blog/building-a-digital-garden/');
  await expect(page.getByRole('navigation', { name: '按合集相邻文章' })).toBeVisible();
  await expect(page.getByRole('button', { name: '复制代码' })).toBeVisible();
  await expect(page.locator('.byline')).toContainText(/\d+ 字/);
  await expect(page.locator('.byline')).toContainText(/约 \d+ 分钟阅读/);
});

test('合集书架按显式章节顺序展示并支持双模式翻页',async({page})=>{await page.goto('/blog/');await expect(page.getByRole('heading',{name:'数字花园札记'})).toBeVisible();const chapters=page.locator('.book li strong');await expect(chapters.nth(0)).toHaveText('把博客当作一座数字花园');await page.goto('/blog/designing-with-constraints/?nav=category');await expect(page.getByRole('button',{name:'按分类'})).toHaveAttribute('aria-pressed','true');await expect(page.getByRole('navigation',{name:'按分类相邻文章'})).toBeVisible()});

test('分类页面展开标题并提供快速索引',async({page},testInfo)=>{await page.goto('/categories/');await expect(page.getByRole('heading',{name:'方法'})).toBeVisible();await expect(page.getByRole('link',{name:/把博客当作一座数字花园/})).toBeVisible();if(testInfo.project.name==='desktop')await expect(page.getByText('快速索引')).toBeVisible();else await expect(page.locator('#category-jump')).toBeVisible()});

test('项目卡片与定制关于页可用',async({page})=>{await page.goto('/projects/');await expect(page.getByRole('heading',{name:'Prism Notes'})).toBeVisible();await expect(page.getByText('SuiYueMengHen/SuiYueMengHen.github.io')).toBeVisible();await page.goto('/about/');await expect(page.getByRole('heading',{name:/慢一点思考/})).toBeVisible();await expect(page.getByRole('heading',{name:'写作原则'})).toBeVisible()});

test('滚动使用浏览器原生路径且 wheel 不被阻止',async({page})=>{await page.goto('/');const prevented=await page.evaluate(()=>{const event=new WheelEvent('wheel',{deltaY:100,cancelable:true});window.dispatchEvent(event);return event.defaultPrevented});expect(prevented).toBe(false);expect(await page.locator('script[src*="SmoothScroll"]').count()).toBe(0)});

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
  await expect.poll(() => page.evaluate(() => localStorage.getItem('prism-reader-settings'))).not.toContain('smoothScroll');
});

test('LaTeX 公式由 MathJax 输出为 SVG', async ({ page }) => {
  await page.goto('/blog/maxwell%E6%96%B9%E7%A8%8B%E7%BB%84/');
  await expect(page.locator('mjx-container[jax="SVG"][display="true"]')).toHaveCount(2);
  await expect(page.locator('mjx-container[jax="SVG"] svg').first()).toBeAttached();
  const font = await page.locator('.prose').evaluate((element) => getComputedStyle(element).fontFamily);
  expect(font).toContain('Computer Modern Serif');
});

test('移动端菜单可以打开', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile', '仅移动端');
  await page.goto('/');
  await page.getByRole('button', { name: '打开菜单' }).click();
  await expect(page.getByRole('navigation', { name: '主导航' })).toBeVisible();
});

test('关键断点无横向溢出',async({page})=>{for(const width of [768,1024,1440]){await page.setViewportSize({width,height:900});for(const route of ['/blog/','/categories/','/projects/','/about/']){await page.goto(route);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)}}});
