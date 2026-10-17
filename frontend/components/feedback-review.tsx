'use client';
import {useState,type FormEvent} from 'react';
import {useResource} from '@/lib/use-resource';
import {post} from '@/lib/api';
import type {Question,Submission} from '@/lib/classroom-types';
import {ErrorPanel,Loading} from './primitives';
type Dispute={id:string;question_id:string;reason:string;status:'open'|'resolved';created_at:string};
type Review={id:string;question_id:string;reason:string;feedback:string;answer_score:number;reasoning_score:number;created_at:string;dispute_id?:string|null};
type ReviewData={submission_id:string;original_evaluation:Submission['evaluation'];evaluation:Submission['evaluation'];reviews:Review[];disputes:Dispute[]};

export function FeedbackReview({submissionId,questions,role,onChanged}:{submissionId:string;questions:Question[];role:'teacher'|'learner';onChanged:()=>void}){
  const resource=useResource<ReviewData>(`/classroom/submissions/${submissionId}/reviews`);
  const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);const [question,setQuestion]=useState(questions[0]?.id||'');
  async function submit(e:FormEvent<HTMLFormElement>){
    e.preventDefault();if(busy)return;const form=e.currentTarget;const f=new FormData(form);setBusy(true);setError(null);
    const body=role==='teacher'?{question_id:question,answer_score:Number(f.get('answer_score')),reasoning_score:Number(f.get('reasoning_score')),feedback:f.get('feedback'),misconception:f.get('misconception')||'',reason:f.get('reason'),...(f.get('dispute_id')?{dispute_id:f.get('dispute_id')}:{})}:{question_id:question,reason:f.get('reason')};
    try{resource.setData(await post<ReviewData>(`/classroom/submissions/${submissionId}/${role==='teacher'?'reviews':'disputes'}`,body));form.reset();onChanged();}catch(err){setError(err);}finally{setBusy(false);}
  }
  return <section className="section-space">{resource.error?<ErrorPanel error={resource.error} retry={resource.reload}/>:resource.loading?<Loading/>:resource.data&&<>
    {resource.data.reviews.length>0&&<div className="notice"><strong>Teacher-reviewed feedback</strong><p>The original AI feedback is preserved. Your teacher’s latest review informs course recommendations.</p></div>}
    <details className="section-space"><summary>{role==='teacher'?'Review or correct feedback':'Ask your teacher to review feedback'}</summary><p className="small muted section-space">{role==='teacher'?'Record your assessment and why it differs. Reviews add to the history; original responses remain intact.':'Explain what the feedback missed or misunderstood. Your teacher can review the reasoning with you.'}</p>{error?<ErrorPanel error={error}/>:null}
      <form className="form-stack section-space" onSubmit={submit}><label>Question to review<select value={question} onChange={e=>setQuestion(e.target.value)}>{questions.map((q,i)=><option key={q.id} value={q.id}>Question {i+1} · {q.topic}</option>)}</select></label>
        {role==='teacher'&&<><div className="two-grid"><label>Answer score (0–100)<input name="answer_score" type="number" min="0" max="100" required/></label><label>Reasoning score (0–100)<input name="reasoning_score" type="number" min="0" max="100" required/></label></div><label>Feedback for the student<textarea name="feedback" required minLength={3} maxLength={2000} rows={3}/></label><label>Concept to revisit (optional)<input name="misconception" maxLength={1000}/></label>
          {resource.data.disputes.some(d=>d.status==='open'&&d.question_id===question)&&<label>Resolve a student request<select name="dispute_id"><option value="">No linked request</option>{resource.data.disputes.filter(d=>d.status==='open'&&d.question_id===question).map(d=><option key={d.id} value={d.id}>{d.reason.slice(0,100)}</option>)}</select></label>}
        </>}
        <label>{role==='teacher'?'Reason for this review':'What should your teacher reconsider?'}<textarea name="reason" required minLength={3} maxLength={2000} rows={3}/></label><button className="button secondary" disabled={busy}>{busy?'Saving…':role==='teacher'?'Save teacher review':'Send review request'}</button>
      </form>
    </details>
    {(resource.data.disputes.length>0||resource.data.reviews.length>0)&&<details className="section-space"><summary>Review history ({resource.data.disputes.length+resource.data.reviews.length})</summary>{resource.data.disputes.map(d=><div className="notice section-space" key={d.id}><span className="badge">Student request · {d.status}</span><p>{d.reason}</p></div>)}{resource.data.reviews.map(r=><div className="notice section-space" key={r.id}><strong>Teacher review · {new Date(r.created_at).toLocaleDateString('en-IN')}</strong><p>Answer {r.answer_score}% · Reasoning {r.reasoning_score}%</p><p>{r.feedback}</p><p className="small muted">Review reason: {r.reason}</p></div>)}{resource.data.original_evaluation&&<details className="section-space"><summary>Original AI feedback</summary>{resource.data.original_evaluation.questions.map(f=><p key={f.question_id}>{f.feedback}</p>)}</details>}</details>}
  </>}</section>;
}
