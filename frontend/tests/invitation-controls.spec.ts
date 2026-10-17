import {test,expect} from '@playwright/test';
import {randomUUID} from 'node:crypto';

test('a teacher replaces a student code through the live classroom without changing existing enrollment',async({page})=>{
  test.skip(!process.env.DATABASE_URL||!process.env.DEMO_PASSWORD,'Requires the local development database.');
  const password='browser-rotation-password-123';
  const username=()=>`rot_student_${randomUUID().replaceAll('-','').slice(0,8)}`;
  const teacherName=`rot_teacher_${randomUUID().replaceAll('-','').slice(0,8)}`;
  expect((await page.request.post('/api/auth/login',{data:{username:'teacher_demo',password:process.env.DEMO_PASSWORD}})).status()).toBe(200);
  const seedCodes=(await (await page.request.get('/api/teacher/invitation')).json()).data;
  expect((await page.request.post('/api/auth/signup',{data:{username:teacherName,password,role:'teacher',invite_code:seedCodes.teacher_code}})).status()).toBe(201);
  const before=(await (await page.request.get('/api/teacher/invitation')).json()).data;
  const existingName=username();
  expect((await page.request.post('/api/auth/signup',{data:{username:existingName,password,role:'learner',invite_code:before.student_code}})).status()).toBe(201);
  expect((await page.request.post('/api/auth/login',{data:{username:teacherName,password}})).status()).toBe(200);
  await page.goto('/teacher');
  await page.getByRole('button',{name:'Show class codes',exact:true}).click();
  await page.getByRole('button',{name:'Replace student code',exact:true}).click();
  await page.getByRole('button',{name:'Confirm replacement',exact:true}).click();
  await expect(page.getByText('Student code replaced. Share the new code for future signups.')).toBeVisible();
  const after=(await (await page.request.get('/api/teacher/invitation')).json()).data;
  expect(after.student_code===before.student_code).toBe(false);
  expect(after.teacher_code===before.teacher_code).toBe(true);
  expect((await page.request.post('/api/auth/signup',{data:{username:username(),password,role:'learner',invite_code:before.student_code}})).status()).toBe(403);
  for(let i=0;i<2;i++)expect((await page.request.post('/api/auth/signup',{data:{username:username(),password,role:'learner',invite_code:after.student_code}})).status()).toBe(201);
  expect((await page.request.post('/api/auth/login',{data:{username:existingName,password}})).status()).toBe(200);
  expect((await page.request.post('/api/auth/login',{data:{username:teacherName,password}})).status()).toBe(200);
  const roster=(await (await page.request.get('/api/teacher/roster')).json()).data;
  expect(roster.learners.some((student:{username:string})=>student.username===existingName)).toBe(true);
  // Hide reusable invitations before leaving the page; this test never captures screenshots.
  await page.getByRole('button',{name:'Hide class codes',exact:true}).click();
});

test('teacher confirms one code replacement and can recover from a stale code',async({page})=>{
  // MOCK: presentation fixture only. Isolated PostgreSQL tests verify actual rotation and signup.
  let codes={teacher_code:'BM-fixture-teacher',student_code:'BMS-fixture-student'};
  const requests:unknown[]=[];let reject=false;
  await page.route('**/api/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    if(path==='/api/auth/me')return route.fulfill({json:{data:{id:'teacher',role:'teacher',username:'Teacher'}}});
    if(path==='/api/teacher/roster')return route.fulfill({json:{data:{learners:[],page:{total:0,limit:12,offset:0,has_more:false,next_offset:null}}}});
    if(path==='/api/teacher/invitation')return route.fulfill({json:{data:codes}});
    if(path==='/api/teacher/invitation/rotate'){
      const body=route.request().postDataJSON();requests.push(body);
      if(reject){codes={...codes,teacher_code:'BM-fixture-another-tab'};return route.fulfill({status:409,json:{error:{code:'INVITATION_CHANGED',message:'This code has already changed. Reload class codes before replacing it again.'}}});}
      codes={...codes,[body.kind+'_code']:'BMS-fixture-new'};
      return route.fulfill({json:{data:codes}});
    }
    return route.fulfill({status:404,json:{error:{message:'Unexpected fixture route'}}});
  });
  await page.goto('/teacher');
  await expect(page.getByText(codes.student_code,{exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Show class codes',exact:true}).click();
  await page.getByRole('button',{name:'Replace student code',exact:true}).click();
  await expect(page.getByText('Existing accounts and class assignments will stay unchanged.')).toBeVisible();
  expect(requests).toHaveLength(0);
  await page.getByRole('button',{name:'Cancel replacement',exact:true}).click();
  expect(requests).toHaveLength(0);
  await page.getByRole('button',{name:'Replace student code',exact:true}).click();
  await page.getByRole('button',{name:'Confirm replacement',exact:true}).click();
  await expect(page.getByText('Student code replaced. Share the new code for future signups.')).toBeVisible();
  await expect(page.getByText('BMS-fixture-new',{exact:true})).toBeVisible();
  await expect(page.getByText('BM-fixture-teacher',{exact:true})).toBeVisible();
  expect(requests).toEqual([{kind:'student',current_code:'BMS-fixture-student'}]);
  reject=true;
  await page.getByRole('button',{name:'Replace teacher code',exact:true}).click();
  await page.getByRole('button',{name:'Confirm replacement',exact:true}).click();
  await expect(page.getByRole('region',{name:'Class invitation codes'}).getByRole('alert')).toContainText('already changed');
  await page.getByRole('button',{name:'Reload class codes',exact:true}).click();
  await expect(page.getByText('BM-fixture-another-tab',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Confirm replacement',exact:true})).toHaveCount(0);
});
