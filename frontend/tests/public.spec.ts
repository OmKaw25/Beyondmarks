import { test, expect } from '@playwright/test';
import {captureLayouts} from './visual-checks';

test('landing explains the full journey and links to account creation', async ({page}) => {
  await page.goto('/');
  await expect(page.getByRole('heading', {level:1})).toContainText(/understand/i);
  await captureLayouts(page,'01-landing');
  await page.getByRole('link', {name:'Start learning', exact:true}).click();
  await expect(page).toHaveURL(/signup/);
  await expect(page.getByLabel('Username', {exact:true})).toBeVisible();
  await captureLayouts(page,'10-signup');
});

test('login is usable by keyboard',async({page})=>{
  await page.goto('/login');
  await page.getByLabel('Username',{exact:true}).focus();
  await page.keyboard.type('keyboard_learner');
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Password',{exact:true})).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeFocused();
});

test('signup prevents invalid input and protects teacher enrollment', async ({page}) => {
  await page.goto('/signup');
  await page.getByLabel('Account type').selectOption('teacher');
  await expect(page.getByLabel('Teacher referral code')).toBeVisible();
  await page.getByLabel('Username', {exact:true}).fill('om');
  await page.getByLabel('Password', {exact:true}).fill('short');
  await page.getByRole('button', {name:'Create account', exact:true}).click();
  await expect(page).toHaveURL(/signup/);
});

test('theme persists and mobile does not overflow', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');
  await page.getByRole('button', {name:'Switch to dark theme'}).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('failed sign-in displays an error without fabricating a session', async ({page}) => {
  await page.goto('/login');
  await page.getByLabel('Username', {exact:true}).fill('learner_a');
  await page.getByLabel('Password', {exact:true}).fill('a-valid-length-password');
  await page.getByRole('button', {name:'Sign in', exact:true}).click();
  await expect(page.locator('.notice[role="alert"]')).toContainText(/database|backend|connect|incorrect/i);
  await expect(page).toHaveURL(/login/);
});

test('proxy rejects a foreign origin and accepts the actual local host', async ({request}) => {
  const data={username:'nonexistent_test',password:'invalid-test-password'};
  const foreign=await request.post('/api/auth/login',{data,headers:{Origin:'https://untrusted.invalid'}});
  expect(foreign.status()).toBe(403);
  const local=await request.post('/api/auth/login',{data,headers:{Origin:'http://127.0.0.1:3000'}});
  expect(local.status()).not.toBe(403);
});
