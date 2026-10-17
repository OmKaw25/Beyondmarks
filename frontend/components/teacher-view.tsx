'use client';
import Link from 'next/link';
import {useState} from 'react';
import {useResource} from '@/lib/use-resource';
import type {Learner,Timeline,EvidenceEvent,Assessment,Hypothesis} from '@/lib/types';
import {AppShell} from './site-shell';
import {Empty,ErrorPanel,Loading,PageHeading,SyntheticBadge,readable,HypothesisCards} from './primitives';
import type {DelayedCheck} from '@/lib/retention-types';
import type {PageInfo} from '@/lib/classroom-types';

function TeacherRetention({learnerId}:{learnerId:string}){
  const resource=useResource<{checks:DelayedCheck[]}>(`/teacher/learners/${learnerId}/retention`);
  return <section className="section-space"><h2>Delayed checks</h2>{resource.loading?<Loading/>:resource.error?<ErrorPanel error={resource.error} retry={resource.reload}/>:resource.data?.checks.length?<div className="two-grid">{resource.data.checks.map(c=><article className="card" key={c.id}>
    <div className="card-top"><span className="badge">{c.status}</span>{c.is_synthetic?<SyntheticBadge/>:<span className="small muted">{c.data_origin==='pilot'?'Pilot activity':'Origin not verified'}</span>}</div>
    <h3>{c.concept} - {c.interval_days}-day check</h3><p className="small muted">Due {new Date(c.due_at).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})}</p>
    {c.completed_at&&<p>Completed {new Date(c.completed_at).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})}</p>}
    {c.completed_at&&c.response&&<details><summary>Submitted answer and reasoning</summary><p><strong>Answer</strong></p><pre className="code-block">{c.response.answer}</pre><p><strong>Written explanation</strong></p><p className="lesson-content">{c.response.explanation}</p><p><strong>Selected reasoning rule:</strong> {readable(c.response.reasoning_tag)}</p>{c.result&&<><p>Answer {c.result.correct?'correct':'needs another look'}; Reasoning choice {c.result.reasoning_supported?'supported':'needs another look'}</p><p className="small muted">{c.result.note}</p></>}</details>}
  </article>)}</div>:<p className="muted">A completed investigation schedules checks after 7 and 30 real days. No delayed result is inferred before the learner takes a check.</p>}</section>;
}

function TeacherCodePanel(){
  const resource=useResource<{teacher_code:string;student_code:string}>('/teacher/invitation');
  const [visible,setVisible]=useState(false);const [copied,setCopied]=useState('');const [copyError,setCopyError]=useState(false);
  async function copy(kind:'teacher_code'|'student_code'){try{await navigator.clipboard.writeText(resource.data![kind]);setCopied(kind);setCopyError(false);}catch{setCopyError(true);}}
  return <section className="card section-space" aria-label="Class invitation codes">
    <h2>Your class codes</h2><p>One code invites teachers. The other enrolls students in your class. Both can be reused.</p>
    {resource.error?<ErrorPanel error={resource.error} retry={resource.reload}/>:resource.loading?<Loading/>:resource.data&&<>
      <button className="button secondary" onClick={()=>setVisible(!visible)}>{visible?'Hide class codes':'Show class codes'}</button>
      {visible&&<div className="two-grid section-space">{(['student_code','teacher_code'] as const).map(kind=><div key={kind}>
        <h3>{kind==='student_code'?'Student enrollment code':'Teacher referral code'}</h3>
        <p className="small muted">{kind==='student_code'?'Students use this at signup to receive your subjects and quizzes.':'Teachers use this to create their own separate class.'}</p>
        <p><code>{resource.data![kind]}</code></p><button className="button secondary" onClick={()=>copy(kind)}>{copied===kind?'Copied':kind==='student_code'?'Copy student code':'Copy teacher code'}</button>
      </div>)}</div>}{copyError&&<p role="status">Select the code and copy it manually.</p>}
    </>}
  </section>;
}

export function TeacherList(){const resource=useResource<Learner[]>('/teacher/learners');return <AppShell><PageHeading eyebrow="TEACHER / MENTOR" title="The thinking behind the answers.">Review evidence, uncertainty, and the learner’s perspective. Every learner has a different story.</PageHeading>{resource.loading?<Loading/>:resource.error?<ErrorPanel error={resource.error} retry={resource.reload}/>:resource.data?.length?<div className="three-grid">{resource.data.map(l=><article className="card" key={l.id}><div className="avatar">{l.username[0].toUpperCase()}</div><h2>{l.username.replaceAll('_',' ')}</h2><p>{l.investigations} investigation{l.investigations!==1?'s':''}</p>{l.is_synthetic && <SyntheticBadge/>}<Link className="button secondary full" href={`/teacher/learners/${l.id}`}>Review evidence →</Link></article>)}</div>:<Empty title="No learners assigned yet">Learner evidence becomes available after an administrator assigns learners to your account.</Empty>}<TeacherCodePanel/></AppShell>;}

function Details({event}:{event:EvidenceEvent}){
  const d=event.details;
  const observation=d.value_json as Record<string,unknown>|undefined;
  const hypothesis=d.evidence_summary as Hypothesis|undefined;
  const lines=[
    ['Interpretation',hypothesis?.label],['Description',hypothesis?.description],
    ['Observation',d.evidence_key?readable(String(d.evidence_key)):null],
    ['Learner explanation',d.explanation||observation?.explanation],
    ['Learner confidence (self-reported)',observation?.confidence?readable(String(observation.confidence)):null],
    ['Context (self-reported)',observation?.context?readable(String(observation.context)):null],
    ['Context note',observation?.context_note],
    ['Learner request',observation?.action?readable(String(observation.action)):null],
    ['Request details',observation?.reason],
    ['System interpretation',d.system_hypothesis_label],
    ['Learner alternative',d.alternative_hypothesis_label],
    ['Learner perspective',d.learner_reason],['Rationale',d.rationale],
    ['Response',d.answer||d.selected_choice],['Confidence',d.confidence_label],
    ['Reason for adaptation',d.reason],
    ['Result',typeof d.correct==='boolean'?(d.correct?'Correct response':'Incorrect response'):null]
  ];
  return <div className="event-details">
    {lines.filter(([,v])=>v).map(([label,value])=><div key={String(label)}><strong>{String(label)}</strong><p>{String(value)}</p></div>)}
    {typeof d.score==='number'&&<p>Relative evidence weight: {Math.round(d.score*100)}%</p>}
    {hypothesis && <div className="evidence-details">
      <strong>Supporting observations</strong>
      {hypothesis.supporting_evidence.length ? <ul>{hypothesis.supporting_evidence.map(k=><li key={k}>{readable(k)}</li>)}</ul> : <p>No distinguishing evidence recorded.</p>}
      <strong>Contradicting observations</strong>
      {hypothesis.contradicting_evidence.length ? <ul>{hypothesis.contradicting_evidence.map(k=><li key={k}>{readable(k)}</li>)}</ul> : <p>No contradicting observations recorded.</p>}
      <p className="small muted">Authored evidence weights are not measured probabilities of learner ability.</p>
    </div>}
    {d.new_assessment_json ? <details><summary>Compare earlier and revised interpretations</summary>
      <div className="two-grid"><section><h3>Earlier interpretation</h3><HypothesisCards assessment={d.old_assessment_json as Assessment}/></section>
      <section><h3>Revised interpretation</h3><HypothesisCards assessment={d.new_assessment_json as Assessment}/></section></div>
    </details>:null}
  </div>;
}

export function TeacherTimeline({id}:{id:string}){const [eventOffset,setEventOffset]=useState(0);const resource=useResource<Timeline & {events_page?:PageInfo}>(`/teacher/learners/${id}/timeline?event_offset=${eventOffset}`);return <AppShell><Link className="text-link" href="/teacher">← Assigned learners</Link><PageHeading eyebrow="EVIDENCE TIMELINE" title={resource.data?`${resource.data.username.replaceAll('_',' ')}’s learning story`:'Learner evidence'}>Submitted reasoning stays intact. New observations build on the story.</PageHeading>{resource.loading?<Loading/>:resource.error?<ErrorPanel error={resource.error} retry={resource.reload}/>:resource.data && <>{resource.data.is_synthetic&&<SyntheticBadge/>}{resource.data.events.length?<div className="timeline">{resource.data.events.map(e=><article className="card timeline-event" key={e.id}><div className="card-top"><span className="badge">{e.kind}</span><time className="small muted">{new Date(e.created_at).toLocaleString('en-IN',{timeZone:'Asia/Kolkata'})}</time></div><h3>{e.investigation}</h3>{e.is_synthetic&&<SyntheticBadge/>}<Details event={e}/></article>)}</div>:<Empty title="The story is just beginning">This learner hasn’t submitted investigation evidence yet.</Empty>}<div className="actions section-space">{resource.data.events_page&&resource.data.events_page.total>resource.data.events_page.limit&&<><button className="button secondary" disabled={eventOffset===0} onClick={()=>setEventOffset(Math.max(0,eventOffset-resource.data!.events_page!.limit))}>Newer evidence</button><span className="small muted">Showing {eventOffset+1}?{eventOffset+resource.data.events.length} of {resource.data.events_page.total}</span><button className="button secondary" disabled={!resource.data.events_page.has_more} onClick={()=>setEventOffset(resource.data!.events_page!.next_offset!)}>Older evidence</button></>}</div><TeacherRetention learnerId={id}/><h2 className="section-space">Sample delayed-check history</h2><div className="two-grid">{resource.data.retention.map(c=><article className="card" key={c.id}>{c.is_synthetic&&<SyntheticBadge/>}<span className="badge">{c.outcome}</span><p>{c.explanation}</p></article>)}</div></>}</AppShell>;}
