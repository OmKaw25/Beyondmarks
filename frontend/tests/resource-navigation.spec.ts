import {test,expect} from '@playwright/test';

test('changing quiz pages hides stale results while loading and recovers from a failed page request',async({page})=>{
  // Presentation/transport fixtures deliberately control response timing; no database behavior is mocked as evidence.
  let release:()=>void=()=>{};
  const held=new Promise<void>(resolve=>{release=resolve;});
  let nextRequests=0;
  await page.route('**/api/**',async route=>{
    const url=new URL(route.request().url());
    if(url.pathname==='/api/auth/me')return route.fulfill({json:{data:{id:'learner',username:'Student',role:'learner'}}});
    if(url.pathname==='/api/classroom'){
      const offset=Number(url.searchParams.get('quiz_offset')||0);
      if(offset===20){
        nextRequests++;
        if(nextRequests===1){await held;return route.fulfill({status:503,json:{error:{message:'This page is temporarily unavailable.'}}});}
      }
      const quizzes=Array.from({length:offset===0?20:1},(_,i)=>({id:`quiz-${offset+i}`,title:`Practice ${offset+i+1}`,subject_id:'subject',status:'published',submission_status:null}));
      return route.fulfill({json:{data:{role:'learner',subjects:[],quizzes,quizzes_page:{offset,limit:20,total:21,has_more:offset===0,next_offset:offset===0?20:null}}}});
    }
    return route.fulfill({status:404,json:{error:{message:'Unexpected fixture route'}}});
  });
  await page.goto('/classroom');
  await expect(page.getByRole('heading',{name:'Practice 1',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Next quizzes',exact:true}).click();
  try{
    await expect(page.getByRole('heading',{name:'Practice 1',exact:true})).toHaveCount(0,{timeout:1500});
    await expect(page.getByRole('status',{name:'Loading'})).toBeVisible();
  }finally{release();}
  await expect(page.locator('.notice.error[role="alert"]')).toContainText('This page is temporarily unavailable.');
  await expect(page.getByRole('heading',{name:'Practice 1',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Try again',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Practice 21',exact:true})).toBeVisible();
  await expect(page.locator('.notice.error[role="alert"]')).toHaveCount(0);
  await page.getByRole('button',{name:'Previous quizzes',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Practice 1',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Practice 21',exact:true})).toHaveCount(0);
});
