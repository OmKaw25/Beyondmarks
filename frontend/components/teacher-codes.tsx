'use client';
import {useRef,useState} from 'react';
import {ApiError,message,post} from '@/lib/api';
import {useResource} from '@/lib/use-resource';
import {ErrorPanel,Loading} from './primitives';

type Codes={teacher_code:string;student_code:string};
type Kind='student'|'teacher';

export function TeacherCodePanel(){
  const resource=useResource<Codes>('/teacher/invitation');
  const [visible,setVisible]=useState(false);
  const [copied,setCopied]=useState('');
  const [copyError,setCopyError]=useState(false);
  const [confirm,setConfirm]=useState<Kind|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [stale,setStale]=useState(false);
  const [notice,setNotice]=useState('');
  const inFlight=useRef(false);
  async function copy(kind:Kind){
    try{await navigator.clipboard.writeText(resource.data![`${kind}_code`]);setCopied(kind);setCopyError(false);}
    catch{setCopyError(true);}
  }
  async function replace(){
    if(!confirm||!resource.data||inFlight.current)return;
    const kind=confirm;inFlight.current=true;setBusy(true);setError('');setNotice('');
    try{
      const updated=await post<Codes>('/teacher/invitation/rotate',{kind,current_code:resource.data[`${kind}_code`]});
      resource.setData(updated);setConfirm(null);setCopied('');setCopyError(false);setStale(false);
      setNotice(`${kind==='student'?'Student':'Teacher'} code replaced. Share the new code for future signups.`);
    }catch(reason){setError(message(reason));setStale(reason instanceof ApiError&&reason.code==='INVITATION_CHANGED');}
    finally{inFlight.current=false;setBusy(false);}
  }
  function reload(){setConfirm(null);setError('');setStale(false);setNotice('');setCopied('');resource.reload();}
  return <section className="card section-space" aria-label="Class invitation codes">
    <h2>Your class codes</h2><p>One code invites teachers. The other enrolls students in your class. Both can be reused.</p>
    {resource.error?<ErrorPanel error={resource.error} retry={resource.reload}/>:resource.loading?<Loading/>:resource.data&&<>
      <button className="button secondary" disabled={busy} onClick={()=>{setVisible(!visible);setConfirm(null);setError('');}}>{visible?'Hide class codes':'Show class codes'}</button>
      {visible&&<div className="two-grid section-space">{(['student','teacher'] as const).map(kind=><div key={kind}>
        <h3>{kind==='student'?'Student enrollment code':'Teacher referral code'}</h3>
        <p className="small muted">{kind==='student'?'Students use this at signup to receive your subjects and quizzes.':'Teachers use this to create their own separate class.'}</p>
        <p><code>{resource.data![`${kind}_code`]}</code></p>
        <div className="actions"><button className="button secondary" disabled={busy} onClick={()=>copy(kind)}>{copied===kind?'Copied':`Copy ${kind} code`}</button>
          <button className="text-button" disabled={busy} onClick={()=>{setConfirm(kind);setError('');setNotice('');setStale(false);}}>Replace {kind} code</button></div>
        {confirm===kind&&<div className="notice section-space">
          <p>The old {kind} code will stop accepting new signups. The other class code will stay the same.</p>
          <p>Existing accounts and class assignments will stay unchanged.</p>
          <div className="actions"><button className="button" disabled={busy||stale} onClick={replace}>{busy?'Replacing code...':'Confirm replacement'}</button>
            <button className="button secondary" disabled={busy} onClick={()=>{setConfirm(null);setError('');}}>Cancel replacement</button></div>
        </div>}
      </div>)}</div>}
      {copyError&&<p role="status">Select the code and copy it manually.</p>}
      {error&&<div role="alert"><p>{error}</p><button className="button secondary" disabled={busy} onClick={reload}>Reload class codes</button></div>}
      {notice&&<p role="status">{notice}</p>}
    </>}
  </section>;
}
