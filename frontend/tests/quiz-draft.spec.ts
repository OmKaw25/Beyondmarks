import {test,expect,type Page} from '@playwright/test';
import {randomUUID} from 'node:crypto';
import type {Quiz} from '../lib/classroom-types';
import {captureLayouts} from './visual-checks';

const password='browser-quiz-draft-password-123';
async function setup(page:Page){
  await page.request.post('/api/auth/login',{data:{username:'teacher_demo',password:process.env.DEMO_PASSWORD}});
  const parent=(await (await page.request.get('/api/teacher/invitation')).json()).data;
  const teacher=await page.request.post('/api/auth/signup',{data:{username:'qd_teacher_'+randomUUID().slice(0,8),password,role:'teacher',invite_code:parent.teacher_code}});
  expect(teacher.status()).toBe(201);
  const codes=(await (await page.request.get('/api/teacher/invitation')).json()).data;
  const classroom=(await (await page.request.get('/api/classroom')).json()).data;
  const subject=classroom.subjects[0];
  const quizzes:Quiz[]=[];
  for(let n=0;n<2;n++){
    const created=await page.request.post('/api/classroom/quizzes',{data:{subject_id:subject.id,title:`Draft recovery ${n+1}`,questions:[{course_id:subject.courses[0].id,prompt:'What value is copied when x = 2; y = x; x = 5?',expected_answer:'2'}]}});
    expect(created.status()).toBe(201);
    const quiz=(await created.json()).data;
    expect((await page.request.post(`/api/classroom/quizzes/${quiz.id}/publish`)).ok()).toBeTruthy();
    quizzes.push(quiz);
  }
  const username='qd_student_'+randomUUID().slice(0,8);
  expect((await page.request.post('/api/auth/signup',{data:{username,password,role:'learner',invite_code:codes.student_code}})).status()).toBe(201);
  await page.goto(`/classroom/quizzes/${quizzes[0].id}`);
  return {quizzes,codes,username};
}
async function keys(page:Page){return page.evaluate(()=>Object.keys(sessionStorage).filter(k=>k.startsWith('bm-quiz-draft:')));}

test.describe('Quiz drafts',()=>{
  test.skip(!process.env.DATABASE_URL||!process.env.DEMO_PASSWORD,'Requires configured database and demo teacher.');
  test('refresh and transport failure preserve writing; quiz and account identities isolate it',async({page})=>{
    const {quizzes,codes,username}=await setup(page);
    const longReason='A'.repeat(3000);
    await page.getByLabel('Your answer to question 1').fill('2');
    await page.getByLabel('Your reasoning for question 1').fill(longReason);
    await page.reload();
    await expect(page.getByLabel('Your answer to question 1')).toHaveValue('2');
    await expect(page.getByLabel('Your reasoning for question 1')).toHaveValue(longReason);
    // Transport failure only: all users, authorization, quizzes and questions use the real API.
    await page.route('**/api/classroom/quizzes/*/submit',route=>route.abort('failed'));
    await page.getByRole('button',{name:'Submit quiz',exact:true}).click();
    await expect(page.getByText('Unable to reach the backend. Check your connection and try again.')).toBeVisible();
    await page.reload();
    await expect(page.getByLabel('Your reasoning for question 1')).toHaveValue(longReason);
    await page.goto(`/classroom/quizzes/${quizzes[1].id}`);
    await expect(page.getByLabel('Your reasoning for question 1')).toHaveValue('');
    // Switch the authenticated session without UI signout, so the old draft remains to test isolation.
    expect((await page.request.post('/api/auth/signup',{data:{username:'qd_student_'+randomUUID().slice(0,8),password,role:'learner',invite_code:codes.student_code}})).status()).toBe(201);
    await page.goto(`/classroom/quizzes/${quizzes[0].id}`);
    await expect(page.getByLabel('Your reasoning for question 1')).toHaveValue('');
    await page.request.post('/api/auth/login',{data:{username,password}});
    await page.reload();
    await expect(page.getByLabel('Your reasoning for question 1')).toHaveValue(longReason);
    await page.getByRole('button',{name:'Sign out',exact:true}).click();
    await expect(page).toHaveURL(/login/);
    expect(await keys(page)).toEqual([]);
  });

  test('saved responses clear drafts, authoritative submitted load clears stale data, and storage errors do not block submission',async({page})=>{
    const {quizzes}=await setup(page);
    await page.getByLabel('Your answer to question 1').fill('2');
    await page.getByLabel('Your reasoning for question 1').fill('The value is copied at assignment.');
    const draftKey=(await keys(page))[0];
    expect(draftKey).toBeTruthy();
    const learnerQuiz=(await (await page.request.get(`/api/classroom/quizzes/${quizzes[0].id}`)).json()).data as Quiz;
    // MOCK: saved/pending transport response avoids an additional external AI request.
    // Real submission persistence and grading are covered by classroom.spec and backend tests.
    const saved:Quiz={...learnerQuiz,submissions:[{id:randomUUID(),learner:'Student',status:'pending',submitted_at:new Date().toISOString(),error_code:'QUOTA_LIMIT',responses:[],evaluation:null}]};
    await page.route(`**/api/classroom/quizzes/${quizzes[0].id}/submit`,route=>route.fulfill({status:201,json:{data:saved}}));
    await page.getByRole('button',{name:'Submit quiz',exact:true}).click();
    await expect(page.getByRole('heading',{name:'Your results',exact:true})).toBeVisible();
    expect(await keys(page)).toEqual([]);
    await page.evaluate(key=>sessionStorage.setItem(key,JSON.stringify({savedAt:Date.now(),values:{}})),draftKey);
    await page.route(`**/api/classroom/quizzes/${quizzes[0].id}?*`,route=>route.fulfill({json:{data:saved}}));
    await page.reload();
    await expect(page.getByRole('heading',{name:'Your results',exact:true})).toBeVisible();
    expect(await keys(page)).toEqual([]);
    await page.goto(`/classroom/quizzes/${quizzes[1].id}`);
    await page.evaluate(()=>{Storage.prototype.setItem=()=>{throw new DOMException('Storage unavailable','QuotaExceededError');};});
    await page.getByLabel('Your answer to question 1').fill('2');
    await page.getByLabel('Your reasoning for question 1').fill('Storage must not stop me explaining my answer.');
    await page.route(`**/api/classroom/quizzes/${quizzes[1].id}/submit`,route=>route.abort('failed'),{times:1});
    await page.getByRole('button',{name:'Submit quiz',exact:true}).click();
    await expect(page.getByText('Unable to reach the backend. Check your connection and try again.')).toBeVisible();
    await page.getByRole('button',{name:'Try again',exact:true}).click();
    await expect(page.getByLabel('Your answer to question 1')).toHaveValue('2');
    await expect(page.getByLabel('Your reasoning for question 1')).toHaveValue('Storage must not stop me explaining my answer.');
    await page.route(`**/api/classroom/quizzes/${quizzes[1].id}/submit`,route=>route.fulfill({status:201,json:{data:{...saved,id:quizzes[1].id}}}));
    await page.getByRole('button',{name:'Submit quiz',exact:true}).click();
    await expect(page.getByRole('heading',{name:'Your results',exact:true})).toBeVisible();
  });

  test('expired drafts are discarded, storage stays bounded and changed questions start empty',async({page})=>{
    const {quizzes}=await setup(page);
    await page.getByLabel('Your answer to question 1').fill('Expired answer');
    const key=(await keys(page))[0];
    await page.evaluate(key=>{
      const old=JSON.parse(sessionStorage.getItem(key)!);old.savedAt=Date.now()-25*60*60*1000;sessionStorage.setItem(key,JSON.stringify(old));
    },key);
    await page.reload();
    await expect(page.getByLabel('Your answer to question 1')).toHaveValue('');
    expect(await keys(page)).toEqual([]);
    await page.evaluate(()=>{
      for(let n=0;n<25;n++)sessionStorage.setItem(`bm-quiz-draft:old-${n}`,JSON.stringify({savedAt:Date.now()-10000+n,values:{}}));
    });
    await page.getByLabel('Your reasoning for question 1').fill('Only this question owns this explanation.');
    expect((await keys(page)).length).toBe(20);
    await page.getByLabel('Your answer to question 1').fill('2');
    await page.getByLabel('Your reasoning for question 1').fill('The assignment copies the current value of x into y. Changing x later does not change y.');
    await page.reload();
    await expect(page.getByLabel('Your answer to question 1')).toHaveValue('2');
    await captureLayouts(page,'25-quiz-draft');
    const learnerQuiz=(await (await page.request.get(`/api/classroom/quizzes/${quizzes[0].id}`)).json()).data as Quiz;
    // MOCK: question identity change verifies draft isolation; published questions are normally immutable.
    const changed={...learnerQuiz,questions:learnerQuiz.questions.map(q=>({...q,id:randomUUID()}))};
    await page.route(`**/api/classroom/quizzes/${quizzes[0].id}?*`,route=>route.fulfill({json:{data:changed}}));
    await page.reload();
    await expect(page.getByLabel('Your reasoning for question 1')).toHaveValue('');
  });
});

test('retrying AI feedback preserves the current teacher response page',async({page})=>{
  // MOCK: presentation fixture for retry response pagination; no grading request is sent.
  const question={id:randomUUID(),course_id:randomUUID(),topic:'Variables',prompt:'What is copied?',expected_answer:'2'};
  const submission=(learner:string)=>({id:learner,learner,status:'pending',submitted_at:new Date().toISOString(),error_code:'QUOTA_LIMIT',responses:[{question_id:question.id,answer:'2',reasoning:'Assignment copies the value.'}],evaluation:null});
  const quiz=(offset:number):Quiz=>({id:'paged',title:'Paged responses',subject:'Programming',subject_id:'subject',role:'teacher',status:'published',questions:[question],submissions:[submission(offset?'Page two student':'Page one student')],submissions_page:{limit:20,offset,total:21,has_more:offset===0,next_offset:offset===0?20:null}});
  await page.route('**/api/**',route=>{
    const url=new URL(route.request().url());
    if(url.pathname==='/api/auth/me')return route.fulfill({json:{data:{id:'teacher',username:'Teacher',role:'teacher'}}});
    if(url.pathname==='/api/classroom')return route.fulfill({json:{data:{role:'teacher',subjects:[],quizzes:[]}}});
    if(url.pathname==='/api/classroom/quizzes/paged')return route.fulfill({json:{data:quiz(Number(url.searchParams.get('submission_offset')||0))}});
    if(url.pathname.endsWith('/retry'))return route.fulfill({json:{data:quiz(0)}});
    if(url.pathname.endsWith('/reviews'))return route.fulfill({json:{data:{reviews:[],disputes:[],evaluation:null,original_evaluation:null}}});
    return route.fulfill({status:404,json:{error:{message:'Unexpected fixture route'}}});
  });
  await page.goto('/classroom/quizzes/paged');
  await page.getByRole('button',{name:'Next responses',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Page two student',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Try feedback again',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Page two student',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Page one student',exact:true})).toHaveCount(0);
  await expect(page.getByText('Showing 21–21 of 21')).toBeVisible();
});
