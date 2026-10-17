'use client';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { ApiError, message } from '@/lib/api';
import type { Assessment } from '@/lib/types';

export function CodeBlock({ code }: { code: string }) { return <pre className="code-block" tabIndex={0} aria-label="Program code"><code>{code}</code></pre>; }
export function SyntheticBadge() { return <p className="synthetic" title="Example data, not recorded learner progress."><span aria-hidden="true">◇</span> Sample activity</p>; }
export function ErrorPanel({ error, retry }: { error: unknown; retry?: () => void }) {
  return <div className="notice error" role="alert"><strong>We couldn’t complete that step.</strong><p>{message(error)}</p><div className="actions">{retry && <button className="button secondary" onClick={retry}>Try again</button>}{error instanceof ApiError && error.status === 401 && <Link className="button" href="/login">Sign in</Link>}</div></div>;
}
export function Loading() { return <div className="loading" role="status" aria-label="Loading"><div className="skeleton wide"/><div className="skeleton"/><div className="skeleton wide"/><span>Loading your workspace…</span></div>; }
export function Empty({ title, children }: { title: string; children: ReactNode }) { return <div className="empty"><span className="empty-icon" aria-hidden="true">◎</span><h2>{title}</h2><p>{children}</p></div>; }
export function PageHeading({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) { return <div className="page-heading"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{children && <p className="lead">{children}</p>}</div>; }
export function readable(key: string) { return key.replace(/^(predicts|challenge):.*/, 'Evidence from the follow-up or learner perspective').replaceAll('_', ' '); }
export function HypothesisCards({ assessment }: { assessment: Assessment }) {
  return <div className="hypothesis-list">{assessment.uncertain && <div className="notice"><strong>More than one explanation is still possible.</strong><p>These are working interpretations. Your perspective and next response can change them.</p></div>}{assessment.hypotheses.map((h, index) => <article className={`card hypothesis ${index === 0 ? 'leading' : ''}`} key={h.id}><div className="card-top"><span className="eyebrow">{index === 0 ? 'Leading interpretation' : 'Another possibility'}</span><span className="badge">{assessment.uncertain ? 'Uncertain' : h.confidence}</span></div><h3>{h.label}</h3><p>{h.description}</p><div className="evidence-meter" aria-hidden="true"><span style={{ width: `${h.score * 100}%` }}/></div><p className="small muted">{Math.round(h.score * 100)}% relative evidence weight</p><details><summary>See the evidence</summary><div className="evidence-details"><strong>Supporting observations</strong>{h.supporting_evidence.length ? <ul>{h.supporting_evidence.map(k => <li key={k}>{readable(k)}</li>)}</ul> : <p>No distinguishing evidence yet.</p>}{h.contradicting_evidence.length > 0 && <><strong>Contradicting observations</strong><ul>{h.contradicting_evidence.map(k => <li key={k}>{readable(k)}</li>)}</ul></>}</div></details></article>)}<p className="small muted">Evidence weights come from authored rules. They are not measured probabilities of your ability. {assessment.limits}</p></div>;
}

const steps = ['investigate', 'diagnosis', 'follow-up', 'support', 'transfer', 'independent', 'reflection'];
const labels = ['Investigate', 'Interpret', 'Follow up', 'Learn', 'Transfer', 'Independent', 'Reflect'];
export function ProgressStepper({ stage }: { stage: string }) { const current = stage === 'retention' ? steps.length : steps.indexOf(stage); return <ol className="stepper" aria-label="Learning journey">{steps.map((step, i) => <li key={step} className={i === current ? 'current' : i < current ? 'done' : ''} aria-current={i === current ? 'step' : undefined}><span>{i < current ? '✓' : i + 1}</span><small>{labels[i]}</small></li>)}</ol>; }
