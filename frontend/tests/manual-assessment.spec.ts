import {test,expect} from '@playwright/test';
import type {Feedback,Quiz,Submission} from '../lib/classroom-types';

test('teacher can assess saved answers during an AI outage and see partial progress',async({page})=>{
  // Presentation fixtures only. PostgreSQL tests cover authorization, persistence and late AI results.
  const questions=[1,2].map(n=>({id:`question-${n}`,course_id:'course',topic:'Evidence',prompt:`Explain claim ${n}.`,expected_answer:'Evidence'}));
  const submission:Submission={id:'saved',learner:'Student',status:'pending',submitted_at:new Date().toISOString(),error_code:'QUOTA_LIMIT',
    responses:questions.map(q=>({question_id:q.id,answer:'Evidence',reasoning:'It supports the claim.'})),evaluation:null,original_evaluation:null,
    assessment:{status:'pending',assessed_questions:0,total_questions:2}};
  const quiz:Quiz={id:'manual',title:'Reason from evidence',subject:'Science',subject_id:'science',status:'published',role:'teacher',questions,submissions:[submission]};
  const reviews:Record<string,unknown>[]=[];
  await page.route('**/api/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    if(path==='/api/auth/me')return route.fulfill({json:{data:{id:'teacher',role:'teacher',username:'Class teacher'}}});
    if(path==='/api/classroom')return route.fulfill({json:{data:{role:'teacher',subjects:[],quizzes:[]}}});
    if(path==='/api/classroom/quizzes/manual')return route.fulfill({json:{data:quiz}});
    if(path==='/api/classroom/submissions/saved/reviews'){
      if(route.request().method()==='POST'){
        const input=route.request().postDataJSON();
        reviews.push({...input,id:`review-${reviews.length}`,created_at:new Date().toISOString()});
        const feedback:Feedback={...input,reviewed:true,needs_review:false};
        submission.evaluation={source:'teacher',questions:[...(submission.evaluation?.questions||[]),feedback]};
        submission.assessment={status:reviews.length===2?'complete':'partial',assessed_questions:reviews.length,total_questions:2};
      }
      return route.fulfill({json:{data:{submission_id:'saved',evaluation:submission.evaluation,original_evaluation:null,reviews,disputes:[]}}});
    }
    return route.fulfill({status:404,json:{error:{message:'Unexpected fixture route'}}});
  });
  await page.goto('/classroom/quizzes/manual');
  await expect(page.getByText('Feedback available for 0 of 2 questions.')).toBeVisible();
  for(let i=0;i<2;i++){
    await page.getByText('Assess saved answers',{exact:true}).click();
    await page.getByLabel('Question to review').selectOption(questions[i].id);
    await page.getByLabel('Answer score (0–100)').fill('80');
    await page.getByLabel('Reasoning score (0–100)').fill('90');
    await page.getByLabel('Feedback for the student').fill('Your evidence supports the explanation.');
    await page.getByLabel('Reason for this review').fill('I assessed the saved answer directly.');
    await page.getByRole('button',{name:'Save teacher review',exact:true}).click();
    await expect(page.getByText(new RegExp(`Feedback available for ${i+1} of 2 questions`))).toBeVisible();
    await expect(page.getByText('Teacher assessment',{exact:true})).toHaveCount(i+1);
    await expect(page.getByText('AI assessment',{exact:true})).toHaveCount(0);
    await expect(page.getByText('The original AI feedback is preserved.',{exact:false})).toHaveCount(0);
  }
  expect(reviews).toHaveLength(2);
  await expect(page.getByText('Awaiting assessment for this question.')).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Try feedback again',exact:true})).toHaveCount(0);
  await expect(page.getByText('AI feedback is temporarily at its usage limit.',{exact:false})).toHaveCount(0);
});

test('classroom cards distinguish pending, partial and completed teacher assessment',async({page})=>{
  // Presentation fixture: AI status intentionally remains pending in all three cards.
  await page.route('**/api/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    if(path==='/api/auth/me')return route.fulfill({json:{data:{id:'learner',role:'learner',username:'Student'}}});
    return route.fulfill({json:{data:{role:'learner',subjects:[],quizzes:[
      {id:'one',title:'Unassessed',status:'published',submission_status:'pending',assessment:{status:'pending',assessed_questions:0,total_questions:2}},
      {id:'two',title:'Partly assessed',status:'published',submission_status:'pending',assessment:{status:'partial',assessed_questions:1,total_questions:2}},
      {id:'three',title:'Fully assessed',status:'published',submission_status:'pending',assessment:{status:'complete',assessed_questions:2,total_questions:2}},
    ]}}});
  });
  await page.goto('/classroom');
  await expect(page.locator('article').filter({has:page.getByRole('heading',{name:'Unassessed',exact:true})})).toContainText('Answers saved');
  await expect(page.locator('article').filter({has:page.getByRole('heading',{name:'Partly assessed',exact:true})})).toContainText('Feedback for 1 of 2');
  await expect(page.locator('article').filter({has:page.getByRole('heading',{name:'Fully assessed',exact:true})})).toContainText('Feedback ready');
});
