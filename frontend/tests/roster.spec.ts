import {test,expect} from '@playwright/test';
import {captureLayouts} from './visual-checks';

test('teacher roster filters students without losing access to class codes',async({page})=>{
  test.skip(!process.env.DATABASE_URL||!process.env.DEMO_PASSWORD,'Requires the local development database.');
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  expect((await page.request.post('/api/auth/login',{data:{username:'teacher_demo',password:process.env.DEMO_PASSWORD}})).status()).toBe(200);
  await page.goto('/teacher');
  await expect(page.getByLabel('Include sample accounts')).not.toBeChecked();
  await page.getByLabel('Include sample accounts').check();
  await page.getByLabel('Find a student',{exact:true}).fill('learner_a');
  await page.getByRole('button',{name:'Search students',exact:true}).click();
  await expect(page.getByRole('heading',{name:'learner a',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'learner b',exact:true})).toHaveCount(0);
  await page.getByLabel('Include sample accounts').uncheck();
  await page.getByRole('button',{name:'Search students',exact:true}).click();
  await expect(page.getByRole('heading',{name:'No students match these filters',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Clear filters',exact:true}).click();
  await expect(page.getByLabel('Find a student',{exact:true})).toHaveValue('');
  await expect(page.getByLabel('Include sample accounts')).not.toBeChecked();
  await expect(page.getByRole('heading',{name:'Your class codes',exact:true})).toBeVisible();
  await captureLayouts(page,'24-teacher-roster');
  expect(errors).toEqual([]);
});
