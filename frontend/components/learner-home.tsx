'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { AppShell } from './site-shell';
import { Empty, ErrorPanel, Loading, PageHeading } from './primitives';
import { useResource } from '@/lib/use-resource';
import { post } from '@/lib/api';
import type { Home, Journey } from '@/lib/types';

export function LearnerHome() {
  const resource = useResource<Home>('/learner/home'); const [busy,setBusy]=useState<string|null>(null); const [error,setError]=useState<unknown>(null); const router=useRouter();
  async function start(id:string) { setBusy(id);setError(null);try { const next=await post<Journey>('/investigations/start',{exercise_id:id});router.push(next.next_url); } catch(e){setError(e);}finally{setBusy(null);} }
  const latestByTopic=new Map<string,Home['attempts'][number]>();
  for(const attempt of [...(resource.data?.attempts||[])].filter(a=>!a.is_synthetic).sort((a,b)=>Date.parse(b.created_at)-Date.parse(a.created_at))){
    if(!latestByTopic.has(attempt.concept))latestByTopic.set(attempt.concept,attempt);
  }
  const attempts=[...latestByTopic.values()];
  const steps=['investigate','diagnosis','follow-up','support','transfer','independent','reflection'];
  const stages:Record<string,string>={investigate:'Investigation in progress',diagnosis:'Review your reasoning','follow-up':'Follow-up question',support:'Learning in progress',transfer:'Practise in a new context',independent:'Independent check',reflection:'Reflection challenge',review:'Ready for teacher review',retention:'Completed'};
  return <AppShell><PageHeading eyebrow="YOUR LEARNING, IN CONTEXT" title={resource.data ? `Welcome, ${resource.data.username.replaceAll('_',' ')}.` : 'Your learning workspace.'}>Pick a concept. Explore your reasoning. Find your next step.</PageHeading>{resource.loading ? <Loading/> : resource.error ? <ErrorPanel error={resource.error} retry={resource.reload}/> : resource.data && <>{error ? <ErrorPanel error={error}/> : null}<section><p><Link className="button secondary" href="/classroom">Open class subjects &amp; quizzes</Link></p><div className="section-bar"><h2>Choose an investigation</h2><span className="small muted">Basic programming</span></div><div className="three-grid">{resource.data.exercises.map((e,i)=><article className="card exercise-card" key={e.id}><div className="card-top"><span className="concept-icon">{['x =','? :','↻'][i%3]}</span><span className="small muted">0{i+1}</span></div><p className="eyebrow">{e.concept}</p>{e.score!==null&&e.score<60&&<p className="badge">Recommended next - latest quiz {e.score}%</p>}<h3>{e.title}</h3><p>Inspect an explanation, share your reasoning, and see where the evidence leads.</p><button className="button secondary full" disabled={!!busy} onClick={()=>start(e.id)}>{busy===e.id ? 'Opening…':'Investigate'} <span aria-hidden="true">↗</span></button></article>)}</div>{!resource.data.exercises.length && <Empty title="Your first investigation is on its way">The workspace administrator needs to load the authored curriculum.</Empty>}</section><section className="section-space"><div className="section-bar"><h2>Your learning history</h2></div>{attempts.length ? <div className="attempt-list">{attempts.map(a=><article className="card attempt-row" key={a.id}><div><span className="badge">{a.status==='complete' ? 'Completed' : stages[a.stage]||'In progress'}</span><h3>{a.concept}</h3><p className="small muted">{a.status==='complete'?'All steps completed':steps.includes(a.stage)?`Step ${steps.indexOf(a.stage)+1} of ${steps.length}`:'Teacher review'}</p></div><Link className="button secondary" href={a.next_url}>{a.status==='complete'?'Review':'Continue'} →</Link></article>)}</div> : <Empty title="Start with a little curiosity">Your explanations, follow-ups, and independent checks will appear here as you learn.</Empty>}</section></>}</AppShell>;
}
