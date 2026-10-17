'use client';
import Link from 'next/link';
import {useState,type FormEvent} from 'react';
import {useResource} from '@/lib/use-resource';
import {post} from '@/lib/api';
import type {Classroom,Quiz,Submission} from '@/lib/classroom-types';
import {QuizForm} from './classroom-view';
import {AppShell} from './site-shell';
import {ErrorPanel,Loading,PageHeading} from './primitives';
import {FeedbackReview} from './feedback-review';

const pendingMessages:Record<string,string>={QUOTA_LIMIT:'AI feedback is temporarily at its usage limit. Your answers are saved.',NOT_CONFIGURED:'Your answers are saved. AI feedback is awaiting setup.',KEY_REJECTED:'Your answers are saved. Your teacher needs to check the AI connection.',MODEL_UNAVAILABLE:'Your answers are saved. The AI service needs a configuration update.'};
function Results({submission,quiz,busy,retry,onChanged}:{submission:Submission;quiz:Quiz;busy:boolean;retry:(id:string)=>void;onChanged:()=>void}){
  return <article className="card section-space"><div className="section-bar"><h2>{quiz.role==='teacher'?submission.learner:'Your results'}</h2><span className="badge">{submission.status==='graded'?(submission.evaluation?.questions.some(f=>f.reviewed)?'Teacher-reviewed feedback':'AI feedback'):'Awaiting feedback'}</span></div>
    {submission.status!=='graded'&&<div className="notice"><p>{pendingMessages[submission.error_code||'']||'Your answers are saved. Feedback is not ready yet.'}</p><button className="button secondary" disabled={busy} onClick={()=>retry(submission.id)}>{busy?'Preparing feedback…':'Try feedback again'}</button></div>}
    {submission.responses.map(r=>{const q=quiz.questions.find(q=>q.id===r.question_id);const feedback=submission.evaluation?.questions.find(f=>f.question_id===r.question_id);return <section className="section-space" key={r.question_id}>
      <p className="eyebrow">{q?.topic}</p><h3 className="lesson-content">{q?.prompt}</h3><div className="two-grid"><div><strong>Answer</strong><p className="lesson-content">{r.answer}</p></div><div><strong>Reasoning</strong><p className="lesson-content">{r.reasoning}</p></div></div>
      {feedback&&<div className="notice"><div className="actions"><span className="badge">Answer: {feedback.answer_score}%</span><span className="badge">Reasoning: {feedback.reasoning_score}%</span>{feedback.needs_review&&<span className="badge warning">Teacher review needed</span>}</div><p className="section-space">{feedback.feedback}</p>{feedback.misconception&&<p><strong>Something to revisit: </strong>{feedback.misconception}</p>}</div>}
    </section>;})}
    {submission.evaluation&&<p className="small muted section-space">AI feedback supports learning and teacher review. It can be mistaken.</p>}
    {submission.status==='graded'&&<FeedbackReview submissionId={submission.id} questions={quiz.questions} role={quiz.role} onChanged={onChanged}/>}
  </article>;
}

export function QuizView({id}:{id:string}){
  const [draft,setDraft]=useState<Record<string,string>>({});
  const classroom=useResource<Classroom>('/classroom');const [editing,setEditing]=useState(false);
  const [submissionOffset,setSubmissionOffset]=useState(0);const resource=useResource<Quiz>(`/classroom/quizzes/${id}?submission_offset=${submissionOffset}`);const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);const quiz=resource.data;
  async function action(path:string,body?:unknown){setBusy(true);setError(null);try{resource.setData(await post<Quiz>(path,body));}catch(e){setError(e);}finally{setBusy(false);}}
  async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();if(busy)return;const f=new FormData(e.currentTarget);await action(`/classroom/quizzes/${id}/submit`,{responses:quiz?.questions.map(q=>({question_id:q.id,answer:f.get(`answer-${q.id}`),reasoning:f.get(`reason-${q.id}`)}))});}
  return <AppShell><Link href="/classroom" className="text-link">← Back to classroom</Link><PageHeading eyebrow={quiz?.subject||'CLASS QUIZ'} title={quiz?.title||'Your quiz'}/>
    {resource.loading?<Loading/>:resource.error?<ErrorPanel error={resource.error} retry={resource.reload}/>:quiz&&<>
      {error?<ErrorPanel error={error} retry={resource.reload}/>:null}
      {quiz.role==='teacher'?<><div className="notice"><strong>{quiz.status==='draft'?'Draft · Only you can see this quiz.':'Published to your class.'}</strong><p>{quiz.status==='draft'?'Check your questions and answer keys. Publishing makes this quiz available to every enrolled student.':'Students can submit once. Their answers, reasoning, and AI feedback appear below.'}</p>{quiz.status==='draft'&&<button className="button" disabled={busy} onClick={()=>action(`/classroom/quizzes/${id}/publish`)}>Publish to class</button>}</div>
        {quiz.status==='draft'&&<button className="button secondary section-space" onClick={()=>setEditing(!editing)}>{editing?'Close editor':'Edit draft'}</button>}{editing&&classroom.data&&<QuizForm subjects={classroom.data.subjects} initial={quiz} done={next=>{resource.setData(next);setEditing(false);}}/>}
        {quiz.questions.map((q,i)=><details className="card section-space" key={q.id}><summary>Question {i+1} · {q.topic}</summary><p className="section-space lesson-content">{q.prompt}</p><strong>Answer key</strong><p className="lesson-content">{q.expected_answer}</p>{q.rubric&&<><strong>Reasoning guidance</strong><p>{q.rubric}</p></>}</details>)}
        <h2 className="section-space">Student responses ({quiz.submissions_page?.total??quiz.submissions.length})</h2>{!quiz.submissions.length&&<p className="muted">Responses will appear after students submit.</p>}
      </>:quiz.submissions.length===0?<form className="form-stack" onSubmit={submit}><p>Answer each question and explain how you reached it. Submit when you are ready; your answers will be saved for your teacher.</p>{quiz.questions.map((q,i)=><section className="card form-stack" key={q.id}><p className="eyebrow">Question {i+1} · {q.topic}</p><h2 className="lesson-content">{q.prompt}</h2><label>Your answer to question {i+1}<textarea name={`answer-${q.id}`} value={draft[`answer-${q.id}`]||''} onChange={e=>setDraft(d=>({...d,[`answer-${q.id}`]:e.target.value}))} required maxLength={3000} rows={2}/></label><label>Your reasoning for question {i+1}<textarea name={`reason-${q.id}`} value={draft[`reason-${q.id}`]||''} onChange={e=>setDraft(d=>({...d,[`reason-${q.id}`]:e.target.value}))} required minLength={3} maxLength={3000} rows={4}/></label></section>)}<p className="small muted">Your answers and reasoning will be sent to Gemini for AI feedback and shared with your teacher. Avoid including personal information in your responses.</p><button className="button" disabled={busy}>{busy?'Saving answers and preparing feedback…':'Submit quiz'}</button></form>:<Link href="/classroom" className="button secondary">See your recommended courses →</Link>}
      {quiz.submissions.map(s=><Results key={s.id} submission={s} quiz={quiz} busy={busy} retry={id=>action(`/classroom/submissions/${id}/retry`)} onChanged={resource.reload}/>)}
      {quiz.role==='teacher'&&quiz.submissions_page&&quiz.submissions_page.total>quiz.submissions_page.limit&&<div className="actions section-space"><button className="button secondary" disabled={submissionOffset===0} onClick={()=>setSubmissionOffset(Math.max(0,submissionOffset-quiz.submissions_page!.limit))}>Previous responses</button><span className="small muted">Showing {submissionOffset+1}–{submissionOffset+quiz.submissions.length} of {quiz.submissions_page.total}</span><button className="button secondary" disabled={!quiz.submissions_page.has_more} onClick={()=>setSubmissionOffset(quiz.submissions_page!.next_offset!)}>Next responses</button></div>}
    </>}
  </AppShell>;
}
