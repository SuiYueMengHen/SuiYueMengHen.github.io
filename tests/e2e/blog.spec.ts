import { expect, test } from '@playwright/test';

test('首页提供放大的粒子化莫比乌斯 Hero 与完整主导航', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /把复杂世界/ })).toBeVisible();
  await expect(page.getByRole('img', { name: /莫比乌斯环/ })).toBeVisible();
  await expect(page.locator('[data-mobius-canvas]')).toBeVisible();
  for (const label of ['首页', '合集', '分类', '归档', '项目', '关于']) await expect(page.locator('#site-nav a', { hasText: label })).toHaveCount(1);
  const colors=await page.locator('[data-prism-hero]').evaluate(element=>({hero:getComputedStyle(element).backgroundColor,page:getComputedStyle(document.body).backgroundColor}));
  expect(colors.hero).toBe(colors.page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
});

test('主题切换持久化且减少动态效果时 Hero 静止', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });await page.goto('/');
  await expect.poll(() => page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior)).toBe('auto');
  await expect.poll(() => page.locator('[data-prism-stage]').evaluate(element => getComputedStyle(element).transform)).toBe('none');
  await page.getByRole('button', { name: '切换明暗主题' }).click();
  await expect.poll(() => page.evaluate(() => localStorage.getItem('prism-theme'))).toMatch(/light|dark/);
});

test('Hero 的标题与莫比乌斯环共享滚动驱动的空间舞台', async ({ page }) => {
  await page.goto('/');const stage=page.locator('[data-prism-stage]');const before=await stage.evaluate(element=>getComputedStyle(element).transform);
  await page.evaluate(() => scrollTo(0, Math.round(innerHeight * .35)));
  await expect.poll(() => stage.evaluate(element=>getComputedStyle(element).transform)).not.toBe(before);
});

test('初始化后的空内容库具有完整而明确的页面状态', async ({ page }) => {
  await page.goto('/blog/');await expect(page.getByRole('heading',{name:'合集书架'})).toBeVisible();await expect(page.getByRole('heading',{name:'书架尚待开卷'})).toBeVisible();
  await page.goto('/categories/');await expect(page.getByRole('heading',{name:'分类目录'})).toBeVisible();await expect(page.getByRole('heading',{name:'分类索引为空'})).toBeVisible();await expect(page.locator('#category-jump')).toHaveCount(0);
  await page.goto('/archive/');await expect(page.getByRole('heading',{name:'归档'})).toBeVisible();await expect(page.getByRole('heading',{name:'时间轴尚未启用'})).toBeVisible();
  await page.goto('/projects/');await expect(page.getByRole('heading',{name:'项目',exact:true})).toBeVisible();await expect(page.getByRole('heading',{name:'项目档案尚为空'})).toBeVisible();
  await page.goto('/about/');await expect(page.getByRole('heading',{name:/慢一点思考/})).toBeVisible();
});

test('移动端菜单可以打开', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile', '仅移动端');await page.goto('/');await page.getByRole('button',{name:'打开菜单'}).click();await expect(page.getByRole('navigation',{name:'主导航'})).toBeVisible();
});

test('滚动保持原生且关键断点无横向溢出', async ({ page }) => {
  for (const width of [375,768,1024,1440]) {await page.setViewportSize({width,height:900});for (const route of ['/','/archive/','/blog/','/categories/','/projects/','/about/']) {await page.goto(route);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);}}
  await page.goto('/');const prevented=await page.evaluate(()=>{const event=new WheelEvent('wheel',{deltaY:100,cancelable:true});window.dispatchEvent(event);return event.defaultPrevented});expect(prevented).toBe(false);
});
