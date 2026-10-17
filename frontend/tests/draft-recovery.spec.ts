import {test,expect,type Page} from '@playwright/test';
import {randomUUID} from 'node:crypto';

async function investigation(page:Page) {
  await page.request.post('/api/auth/login',{data:{username:'teacher_demo',password:process.env.DEMO_PASSWORD}});
  const codes=(await (await page.request.get('/api/teacher/invitation')).json()).data;
  const signup=await page.request.post('/api/auth/signup',{data:{username:'draft_'+randomUUID().slice(0,8),password:'browser-test-password-123',role:'learner',invite_code:codes.student_code}});
  expect(signup.status()).toBe(201);
  const home=(await (await page.request.get('/api/learner/home')).json()).data;
  const exercise=home.exercises.find((e:{concept:string})=>/variables/i.test(e.concept));
  const j=(await (await page.request.post('/api/investigations/start',{data:{exercise_id:exercise.id}})).json()).data;
  await page.goto(j.next_url);
  return j;
}

test.describe('Learner draft recovery',()=>{
  test.skip(!process.env.DATABASE_URL||!process.env.DEMO_PASSWORD,'Requires configured development database and demo teacher.');
  test('refresh and a failed request preserve reasoning, while submission and sign out remove drafts',async({page})=>{
    const j=await investigation(page);
    await page.getByRole('checkbox',{name:/saved stays connected/}).check();
    await page.getByLabel('Broad issue category').selectOption('Output');
    await page.getByLabel('Specific reason').selectOption('output_format');
    await page.getByLabel('Explain your reasoning').fill('My unfinished explanation should survive a refresh.');
    await page.getByText('Add confidence or context (optional)',{exact:true}).click();
    await page.getByLabel('How sure do you feel?').selectOption('unsure');
    await page.getByLabel('Anything else you want your teacher to know?').fill('I want time to consider this.');
    await page.reload();
    await expect(page.getByLabel('Explain your reasoning')).toHaveValue('My unfinished explanation should survive a refresh.');
    await expect(page.getByRole('checkbox',{name:/saved stays connected/})).toBeChecked();
    await expect(page.getByLabel('Broad issue category')).toHaveValue('Output');
    await expect(page.getByLabel('Specific reason')).toHaveValue('output_format');
    await page.getByText('Add confidence or context (optional)',{exact:true}).click();
    await expect(page.getByLabel('How sure do you feel?')).toHaveValue('unsure');
    await expect(page.getByLabel('Anything else you want your teacher to know?')).toHaveValue('I want time to consider this.');
    await page.route(`**/api/investigations/${j.id}/correction`,route=>route.abort('failed'));
    await page.getByRole('button',{name:/Explore my reasoning/}).click();
    await expect(page.locator('.notice.error[role="alert"]')).toBeVisible();
    await page.reload();
    await expect(page.getByLabel('Explain your reasoning')).toHaveValue('My unfinished explanation should survive a refresh.');
    await page.unroute(`**/api/investigations/${j.id}/correction`);
    await page.getByRole('button',{name:/Explore my reasoning/}).click();
    await expect(page).toHaveURL(/diagnosis/);
    expect(await page.evaluate(()=>Object.keys(sessionStorage).filter(key=>key.startsWith('bm-draft:')))).toEqual([]);
    await page.getByRole('button',{name:'I disagree',exact:true}).click();
    await page.getByLabel('Another interpretation').selectOption({index:1});
    await page.getByLabel(/What would you like us to know/).fill('A private unfinished perspective.');
    await page.getByRole('button',{name:'Sign out',exact:true}).click();
    await expect(page).toHaveURL(/login/);
    expect(await page.evaluate(()=>Object.keys(sessionStorage).filter(key=>key.startsWith('bm-draft:')))).toEqual([]);
  });

  test('a new attempt never restores another attempt and storage failures do not block submission',async({page})=>{
    const j=await investigation(page);
    await page.getByLabel('Explain your reasoning').fill('Only the first attempt owns this draft.');
    const home=(await (await page.request.get('/api/learner/home')).json()).data;
    const other=home.exercises.find((exercise:{id:string})=>exercise.id!==j.exercise.id);
    const next=(await (await page.request.post('/api/investigations/start',{data:{exercise_id:other.id}})).json()).data;
    expect(next.id).not.toBe(j.id);
    await page.goto(next.next_url);
    await expect(page.getByLabel('Explain your reasoning')).toHaveValue('');
    await page.goto(j.next_url);
    await expect(page.getByLabel('Explain your reasoning')).toHaveValue('Only the first attempt owns this draft.');
    await page.evaluate(()=>{Storage.prototype.setItem=()=>{throw new DOMException('Storage unavailable','QuotaExceededError');};});
    await page.getByRole('checkbox',{name:/saved stays connected/}).check();
    await page.getByLabel('Broad issue category').selectOption('Output');
    await page.getByLabel('Specific reason').selectOption('output_format');
    await page.getByLabel('Explain your reasoning').fill('The output requires more careful investigation.');
    await page.getByRole('button',{name:/Explore my reasoning/}).click();
    await expect(page).toHaveURL(/diagnosis/);
  });

  test('a fresh verification task never inherits the failed answer or explanation',async({page})=>{
    let j=await investigation(page);
    const base='/api/investigations/'+j.id;
    const flawed=j.exercise.segments.find((segment:{text:string})=>/saved stays connected/i.test(segment.text));
    await page.request.post(base+'/correction',{data:{segment_ids:[flawed.id],broad_category:'Output',specific_reason:'output_format',explanation:'I am unsure which assignment matters.'}});
    j=(await (await page.request.post(base+'/select-follow-up')).json()).data;
    if(j.stage==='follow-up')j=(await (await page.request.post(base+'/follow-up',{data:{answer:'3'}})).json()).data;
    await page.request.post(base+'/support',{data:{support_id:j.support.id,answer:'4'}});
    j=(await (await page.request.post(base+'/continue-support',{data:{support_id:j.support.id}})).json()).data;
    const firstTask=j.task.id;
    await page.goto(j.next_url);
    await page.getByRole('radio',{name:'stock = saved',exact:true}).check();
    await page.getByLabel('Explain how your change meets the requirement.').fill('The wrong answer must not reappear on a new task.');
    await page.getByRole('radio',{name:'Changing stock automatically changes every variable copied from it.',exact:true}).check();
    await page.reload();
    await expect(page.getByLabel('Explain how your change meets the requirement.')).toHaveValue('The wrong answer must not reappear on a new task.');
    await expect(page.getByRole('radio',{name:'stock = saved',exact:true})).toBeChecked();
    await page.getByRole('button',{name:/Apply my fix/}).click();
    await expect(page).toHaveURL(/support/);
    await page.getByRole('radio',{name:'5',exact:true}).check();
    await page.getByRole('button',{name:/Check my prediction/}).click();
    await page.getByRole('button',{name:/Continue to the next check/}).click();
    await expect(page).toHaveURL(/transfer/);
    j=(await (await page.request.get(base)).json()).data;
    expect(j.task.id).not.toBe(firstTask);
    await expect(page.locator('textarea[name="explanation"]')).toHaveValue('');
    expect(await page.getByRole('radio').evaluateAll(inputs=>inputs.some(input=>(input as HTMLInputElement).checked))).toBe(false);
  });
});
