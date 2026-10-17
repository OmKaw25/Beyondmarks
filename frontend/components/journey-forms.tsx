'use client';
import { useState, type FormEvent } from 'react';
import {journeyDraftKey,useFormDraft} from '@/lib/use-form-draft';
import type { Journey, Choice } from '@/lib/types';
import { CodeBlock, HypothesisCards } from './primitives';

type Submit = (endpoint:string, body?:unknown)=>Promise<void>;
type Props = { journey:Journey; submit:Submit; busy:boolean };

function RadioChoices({options,name='answer'}:{options:Choice[];name?:string}) { return <div className="choice-list">{options.map(c=><label className="choice" key={c.value}><input required type="radio" name={name} value={c.value}/><span>{c.label}</span></label>)}</div>; }

function selfReport(form:FormData) {
  return {confidence:form.get('confidence')||null,context:form.get('context')||null,context_note:form.get('context_note')||''};
}

function SelfReportFields(){
  return <details><summary>Add confidence or context (optional)</summary><div className="form-stack section-space">
    <p className="small muted">Your perspective is saved for you and your teacher. It does not change whether an answer is correct or prove why a difficulty happened.</p>
    <label>How sure do you feel?<select name="confidence" defaultValue=""><option value="">Prefer not to say</option><option value="unsure">Unsure</option><option value="somewhat_sure">Somewhat sure</option><option value="very_sure">Very sure</option></select></label>
    <label>Did anything affect this response?<select name="context" defaultValue=""><option value="">Prefer not to say</option><option value="none">Nothing I want to add</option><option value="time_pressure">I felt short of time</option><option value="incomplete_work">I had not finished working it out</option><option value="misread">I may have misread the task</option><option value="other">Something else</option></select></label>
    <label>Anything else you want your teacher to know?<textarea name="context_note" rows={2} maxLength={1000}/></label>
  </div></details>;
}

export function AgencyControls({journey:j,submit,busy}:Props){
  const [reason,setReason]=useState('');
  return <section className="card section-space" aria-label="Your learning choices">
    <div className="card-top"><h2>Your pace, your perspective</h2>{j.agency?.paused && <span className="badge">Paused</span>}</div>
    <p className="small muted">Pause at this step or ask your teacher to review your evidence. A help request is saved for their next review.</p>
    {j.agency?.help_requested && <p className="notice" role="status">Your help request is recorded for your teacher{j.agency.help_reason ? `: ${j.agency.help_reason}` : '.'}</p>}
    <details><summary>Add a note for your teacher (optional)</summary><label>What would help?<textarea value={reason} onChange={e=>setReason(e.target.value)} maxLength={1000} rows={2}/></label></details>
    <div className="actions section-space">
      {j.status==='active' && <button className="button secondary" disabled={busy} onClick={()=>submit('agency',{action:j.agency?.paused?'resume':'pause',reason})}>{j.agency?.paused?'Resume this step':'Pause for now'}</button>}
      <button className="button secondary" disabled={busy||j.agency?.help_requested} onClick={()=>submit('agency',{action:'help',reason})}>{j.agency?.help_requested?'Help requested':'Ask my teacher for help'}</button>
    </div>
  </section>;
}

export function InvestigationForm({journey:j,submit,busy}:Props){
  const [category,setCategory]=useState(Object.keys(j.exercise?.categories||{})[0]||'');const [error,setError]=useState('');
  const draft=useFormDraft(journeyDraftKey(j),values=>{const saved=values.category?.[0];if(saved&&j.exercise?.categories[saved])setCategory(saved);});
  async function send(event:FormEvent<HTMLFormElement>){event.preventDefault();const f=new FormData(event.currentTarget);const segments=f.getAll('segment');if(!segments.length){setError('Select at least one explanation segment to investigate.');return;}setError('');await submit('correction',{segment_ids:segments,broad_category:category,specific_reason:f.get('reason'),explanation:f.get('explanation'),...selfReport(f)});}
  if(!j.exercise)return null;
  return <div className="task-grid"><section className="card question-card"><p className="eyebrow">THE INVESTIGATION</p><h2>Read the code. Question the explanation.</h2><p>{j.exercise.prompt}</p><CodeBlock code={j.exercise.code}/><div className="expected"><span>Expected output</span><code>{j.exercise.expected_output}</code></div><div className="notice"><strong>Your thinking matters here.</strong><p>Finding a flaw is one piece of evidence. Explain the reason so we can understand your approach.</p></div></section><section className="card"><p className="eyebrow">YOUR REASONING</p><h2>What doesn’t add up?</h2><form {...draft} className="form-stack" onSubmit={send}><fieldset><legend>Select the flawed part of this explanation</legend>{j.exercise.segments.map(s=><label className="segment-choice" key={s.id}><input name="segment" type="checkbox" value={s.id}/><span>{s.text}</span></label>)}</fieldset>{error && <p role="alert" className="field-error">{error}</p>}<label>Broad issue category<select name="category" value={category} onChange={e=>{setCategory(e.target.value);const reason=e.currentTarget.form?.elements.namedItem("reason");if(reason instanceof HTMLSelectElement)reason.value="";}}>{Object.keys(j.exercise.categories).map(c=><option key={c}>{c}</option>)}</select></label><label>Specific reason<select name="reason" key={category} required defaultValue=""><option value="" disabled>Choose a reason</option>{j.exercise.categories[category]?.map(r=><option value={r.value} key={r.value}>{r.label}</option>)}</select></label><label>Explain your reasoning<textarea name="explanation" required minLength={3} maxLength={2000} rows={4} placeholder="Which step led you to that conclusion?"/></label><SelfReportFields/><button className="button full" disabled={busy}>{busy?'Saving your reasoning…':'Explore my reasoning'} →</button></form></section></div>;
}

export function DiagnosisForm({journey:j,submit,busy}:Props){
  const [disagree,setDisagree]=useState(false);
  const draft=useFormDraft(journeyDraftKey(j));
  if(!j.assessment)return null;
  async function challenge(event:FormEvent<HTMLFormElement>){event.preventDefault();const f=new FormData(event.currentTarget);await submit('challenge',{alternative_hypothesis_id:f.get('alternative'),reason:f.get('reason')});setDisagree(false);}
  return <div className="task-grid"><section><HypothesisCards assessment={j.assessment}/>{j.self_report && <div className="notice"><strong>Your reported perspective</strong><p>{j.self_report.confidence?.replaceAll('_',' ')}{j.self_report.context ? ` - ${j.self_report.context.replaceAll('_',' ')}` : ''}</p><p>{j.self_report.context_note}</p><p className="small muted">Saved alongside the evidence; not a verified cause.</p></div>}</section><aside className="card sticky-card"><p className="eyebrow">YOU HAVE A SAY</p><h2>Does this fit your experience?</h2><p>This is an interpretation of the evidence, and it can change. You know something about your thinking that the system may have missed.</p>{j.challenge ? <div className="notice"><strong>Your perspective is recorded.</strong><p>{j.challenge.alternative}</p>{j.challenge.reason && <p>“{j.challenge.reason}”</p>}</div> : disagree ? <form {...draft} className="form-stack" onSubmit={challenge}><label>Another interpretation<select name="alternative" required defaultValue=""><option value="" disabled>Choose an explanation</option>{j.assessment.hypotheses.slice(1).map(h=><option key={h.id} value={h.id}>{h.label}</option>)}</select></label><label>What would you like us to know? <span className="small muted">Optional</span><textarea name="reason" maxLength={2000} rows={4}/></label><button className="button" disabled={busy}>Record my perspective</button><button type="button" className="text-button" onClick={()=>setDisagree(false)}>Cancel</button></form> : <div className="form-stack"><button className="button" disabled={busy} onClick={()=>submit('select-follow-up')}>This fits — continue →</button><button className="button secondary" disabled={busy} onClick={()=>setDisagree(true)}>I disagree</button></div>}{j.challenge && <button className="button full" disabled={busy} onClick={()=>submit('select-follow-up')}>Find a useful follow-up →</button>}<p className="small muted section-space">Disagreeing is part of learning. It will be visible in your teacher’s evidence view.</p></aside></div>;
}

export function FollowupForm({journey:j,submit,busy}:Props){
  const draft=useFormDraft(journeyDraftKey(j));
  if(!j.followup)return null;
  async function send(e:FormEvent<HTMLFormElement>){e.preventDefault();await submit('follow-up',{answer:new FormData(e.currentTarget).get('answer')});}
  return <div className="focused"><div className="card"><p className="eyebrow">ONE USEFUL NEXT QUESTION</p><h2>{j.followup.prompt}</h2><p>One short interaction to help us understand what your first response couldn’t show.</p><CodeBlock code={j.followup.code}/><form {...draft} className="form-stack" onSubmit={send}><fieldset><legend>Your prediction</legend><RadioChoices options={j.followup.choices}/></fieldset><button className="button" disabled={busy}>{busy?'Recording…':'Share my prediction'} →</button></form></div>{j.selection && <details className="card rationale"><summary>Why this question?</summary><p>{j.selection.rationale}</p><div className="prediction-grid">{j.selection.prediction_labels.map(p=><div key={p.hypothesis}><strong>{p.hypothesis}</strong><p>Predicted response: <code>{p.answer}</code></p></div>)}</div><p className="small muted">These are authored predictions, not conclusions about what you must think.</p></details>}</div>;
}

export function SupportForm({journey:j,submit,busy}:Props){
  const draft=useFormDraft(journeyDraftKey(j));
  if(!j.support)return null;
  async function send(e:FormEvent<HTMLFormElement>){e.preventDefault();await submit('support',{support_id:j.support?.id,answer:new FormData(e.currentTarget).get('answer')});}
  return <div className="focused"><section className="card">
    <p className="eyebrow">A LITTLE SUPPORT, WITH A PURPOSE</p>
    <h2>{j.support.title}</h2><p className="lead">{j.support.explanation}</p>
    <h3>A worked example</h3><CodeBlock code={j.support.worked_example}/>
    {j.support_completed ? <button className="button" disabled={busy} onClick={()=>submit('continue-support',{support_id:j.support?.id})}>{j.result?.correct===false?'Try a fresh example':'Continue to the next check'} →</button> :
      <form {...draft} className="form-stack" onSubmit={send}>
        <fieldset><legend>{j.support.prediction_prompt}</legend><RadioChoices options={j.support.choices_json}/></fieldset>
        <button className="button" disabled={busy}>Check my prediction →</button>
      </form>}
  </section></div>;
}

export function VerificationForm({journey:j,submit,busy}:Props){
  const draft=useFormDraft(journeyDraftKey(j));
  if(!j.task)return null;
  const interaction=j.task.interaction;
  const independent=j.stage==='independent';const reflection=j.stage==='reflection';
  async function send(e:FormEvent<HTMLFormElement>){
    e.preventDefault();const f=new FormData(e.currentTarget);
    const answer=interaction?.format==='multi-output' ? interaction.answer_fields?.map((_,i)=>String(f.get(`answer_${i}`)||'').trim()).join('\n') : f.get('answer');
    await submit(j.stage,{task_id:j.task?.id,answer,explanation:f.get('explanation'),reasoning_tag:f.get('reason'),...selfReport(f)});
  }
  return <div className="focused"><section className="card">
    <div className="card-top"><p className="eyebrow">{reflection?'REFLECT · TEST THE RULE':independent?'INDEPENDENT · FOLLOW THE WHOLE PROGRAM':'TRANSFER · REPAIR THE CODE'}</p><span className="badge">{interaction?.difficulty||'Apply'}</span></div>
    <h2>{j.task.prompt}</h2><p>{interaction?.instruction}</p>
    {independent && <p className="small muted">Work through this on your own, without hints or other tools.</p>}
    <CodeBlock code={j.task.code}/>
    <form {...draft} className="form-stack" onSubmit={send}>
      {interaction?.format==='multi-output' ? <div className="two-grid">{interaction.answer_fields?.map((label,i)=><label key={label}>{label}<input name={`answer_${i}`} required maxLength={200} autoComplete="off"/></label>)}</div> : interaction?.choices ?
        <fieldset><legend>{interaction.answer_label}</legend><RadioChoices options={interaction.choices}/></fieldset> :
        <label>What does the program print?<input name="answer" required maxLength={500} autoComplete="off"/></label>}
      <label>{j.task.explanation_prompt}<textarea name="explanation" required minLength={3} maxLength={2000} rows={4}/></label>
      <fieldset><legend>Which rule supports your answer?</legend><RadioChoices name="reason" options={j.task.reasoning_options}/></fieldset>
      <SelfReportFields/><p className="small muted">Your answer and selected rule are checked together. Your teacher can review your written explanation.</p>
      <button className="button" disabled={busy}>{busy?'Saving…':reflection?'Complete the challenge':independent?'Check my solution':'Apply my fix'} →</button>
    </form>
  </section></div>;
}
