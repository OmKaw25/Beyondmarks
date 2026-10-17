'use client';
import Link from 'next/link';
import {useState,type FormEvent} from 'react';
import {useResource} from '@/lib/use-resource';
import {post} from '@/lib/api';
import type {DelayedCheck} from '@/lib/retention-types';
import {AppShell} from './site-shell';
import {CodeBlock,ErrorPanel,Loading,PageHeading} from './primitives';

export function DelayedCheckView({id}:{id:string}){
  const resource=useResource<DelayedCheck>(`/retention/checks/${id}`);
  const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);
  const check=resource.data;const task=check?.task;const config=task?.interaction;
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();if(busy)return;setBusy(true);setError(null);const f=new FormData(event.currentTarget);
    const answer=config?.format==='multi-output'?config.answer_fields?.map((_,i)=>String(f.get(`answer_${i}`)||'').trim()).join('\n'):String(f.get('answer')||'');
    try{resource.setData(await post<DelayedCheck>(`/retention/checks/${id}/submit`,{answer,explanation:f.get('explanation'),reasoning_tag:f.get('reasoning_tag')}));}catch(e){setError(e);}finally{setBusy(false);}
  }
  return <AppShell><Link className="text-link" href="/retention">← Learning over time</Link><PageHeading eyebrow={check?.concept||'LEARNING OVER TIME'} title={check?`Your ${check.interval_days}-day check`:'A fresh perspective.'}>Try a different problem independently, without hints or other tools.</PageHeading>
    {resource.loading?<Loading/>:resource.error?<ErrorPanel error={resource.error} retry={resource.reload}/>:check&&<>
      {check.is_synthetic&&<p className="notice">Sample activity · This record demonstrates the workflow.</p>}
      {error?<ErrorPanel error={error}/>:null}
      {check.status==='scheduled'?<div className="notice"><h2>Your check is scheduled.</h2><p>It opens {new Date(check.due_at).toLocaleString('en-IN',{timeZone:'Asia/Kolkata'})} IST. This check waits for the real interval.</p></div>:check.status==='due'&&task?<section className="card focused"><p className="eyebrow">INDEPENDENT · NO HINTS</p><h2>{task.prompt}</h2><p>{config?.instruction}</p><CodeBlock code={task.code}/>
        <form className="form-stack" onSubmit={submit}>
          {config?.format==='multi-output'?<div className="two-grid">{config.answer_fields?.map((label,i)=><label key={i}>{label}<input name={`answer_${i}`} required maxLength={200} autoComplete="off"/></label>)}</div>:config?.choices?<fieldset><legend>{config.answer_label||'Your answer'}</legend><div className="choice-list">{config.choices.map(c=><label className="choice" key={c.value}><input type="radio" name="answer" value={c.value} required/>{c.label}</label>)}</div></fieldset>:<label>Your answer<input name="answer" required maxLength={500}/></label>}
          <label>{task.explanation_prompt}<textarea name="explanation" required minLength={3} maxLength={2000} rows={4}/></label>
          <fieldset><legend>Which rule supports your answer?</legend><div className="choice-list">{task.reasoning_options.map(c=><label className="choice" key={c.value}><input type="radio" name="reasoning_tag" value={c.value} required/>{c.label}</label>)}</div></fieldset>
          <p className="small muted">Your answer and selected rule are checked together. Your teacher can review your explanation.</p><button className="button" disabled={busy}>{busy?'Saving your check…':'Submit delayed check'}</button>
        </form></section>:<section className="card"><span className="badge">{check.status==='passed'?'Delayed check passed':'More practice recommended'}</span><h2>{check.status==='passed'?'You applied the idea after a delay.':'Let’s revisit the idea in a new way.'}</h2><p>{check.result?.note||'Your response is saved in your learning history.'}</p>{check.status==='failed'&&check.next_url&&<Link className="button" href={check.next_url}>Continue with fresh practice →</Link>}</section>}
    </>}
  </AppShell>;
}
