'use client';
import Link from 'next/link';
import {useResource} from '@/lib/use-resource';
import type {DelayedCheck} from '@/lib/retention-types';
import {Empty,ErrorPanel,Loading} from './primitives';

export function RetentionPanel(){
  const resource=useResource<{checks:DelayedCheck[]}>('/retention/checks');
  if(resource.loading)return <Loading/>;
  if(resource.error)return <ErrorPanel error={resource.error} retry={resource.reload}/>;
  const checks=(resource.data?.checks||[]).filter(check=>!check.is_synthetic&&check.data_origin!=='demo');
  return <section className="section-space"><div className="section-bar"><h2>Your learning over time</h2><button className="text-button" onClick={resource.reload}>Refresh checks</button></div><p className="muted">A fresh problem after a real delay helps you see what stayed with you. Scheduled checks open when their date arrives.</p>
    {checks.length?<div className="two-grid">{checks.map(c=><article className="card" key={c.id}><div className="card-top"><span className="eyebrow">{c.concept}</span><span className={`badge ${c.status==='passed'?'success':c.status==='due'||c.status==='failed'?'warning':''}`}>{({scheduled:'Scheduled',due:'Ready now',passed:'Check passed',failed:'Needs another look'})[c.status]}</span></div><h3>{c.interval_days}-day check</h3>
      <p>{c.status==='scheduled'?'Your next check is scheduled. There is no need to repeat the same questions today.':c.status==='due'?'Try a new situation on your own, without hints or other tools.':c.status==='passed'?'You solved this delayed check. This is evidence from one check, and your learning continues.':'This check suggests another look at the concept would help.'}</p>
      <p className="small muted">{c.completed_at?'Completed':'Available'} {new Date(c.completed_at||c.due_at).toLocaleString('en-IN',{timeZone:'Asia/Kolkata',dateStyle:'medium',timeStyle:'short'})} IST</p>{c.status!=='scheduled'&&<Link className="button secondary" href={`/retention/checks/${c.id}`}>{c.status==='due'?'Start fresh check':'Review check'} →</Link>}
    </article>)}</div>:<Empty title="No follow-up checks yet">Complete an investigation to schedule your 7-day and 30-day checks.</Empty>}
  </section>;
}
