'use client';

import {useCallback,useEffect,useRef,type FormEvent} from 'react';
import type {Quiz} from './classroom-types';

export const QUIZ_DRAFT_PREFIX='bm-quiz-draft:';
const MAX_AGE=24*60*60*1000;
const MAX_DRAFTS=20;
type Draft={savedAt:number;values:Record<string,string>};

function remove(key:string){try{sessionStorage.removeItem(key);}catch{}}
function read(key:string):Draft|null{
  try{
    const raw=sessionStorage.getItem(key);if(!raw)return null;
    const draft=JSON.parse(raw) as Draft;
    if(!draft||!Number.isFinite(draft.savedAt)||draft.savedAt>Date.now()||Date.now()-draft.savedAt>MAX_AGE||!draft.values||typeof draft.values!=='object'||Array.isArray(draft.values)||Object.keys(draft.values).length>40||Object.entries(draft.values).some(([name,value])=>! /^(answer|reason)-[a-f0-9-]{36}$/.test(name)||typeof value!=='string'||value.length>3000)){
      remove(key);return null;
    }
    return draft;
  }catch{remove(key);return null;}
}

/** A local, unsubmitted learner draft. Never stores teacher answer keys or feedback. */
export function useQuizDraft(quiz:Quiz|null){
  // Survives a request retry's temporary form unmount, including blocked browser storage.
  // This cache belongs to this mounted page; it is not a cross-refresh backup.
  const memory=useRef(new Map<string,Draft>());
  const key=quiz?.role==='learner'&&quiz.viewer_id?`${QUIZ_DRAFT_PREFIX}${quiz.viewer_id}:${quiz.id}:${quiz.questions.map(q=>q.id).join(',')}`:null;
  const submitted=Boolean(quiz?.submissions.length);
  const clear=useCallback(()=>{if(key){memory.current.delete(key);remove(key);}},[key]);
  useEffect(()=>{if(submitted)clear();},[submitted,clear]);
  const ref=useCallback((form:HTMLFormElement|null)=>{
    if(!form||!key||submitted)return;
    const cached=memory.current.get(key);
    if(cached&&Date.now()-cached.savedAt>MAX_AGE)memory.current.delete(key);
    const draft=memory.current.get(key)||read(key);if(!draft)return;
    for(const field of Array.from(form.elements))if(field instanceof HTMLTextAreaElement&&Object.hasOwn(draft.values,field.name))field.value=draft.values[field.name];
  },[key,submitted]);
  function onChange(event:FormEvent<HTMLFormElement>){
    if(!key||submitted)return;
    const values:Record<string,string>={};
    for(const field of Array.from(event.currentTarget.elements))if(field instanceof HTMLTextAreaElement&&/^(answer|reason)-[a-f0-9-]{36}$/.test(field.name))values[field.name]=field.value.slice(0,3000);
    const draft={savedAt:Date.now(),values};
    memory.current.delete(key);memory.current.set(key,draft);
    for(const [candidate,stored] of memory.current)if(Date.now()-stored.savedAt>MAX_AGE||memory.current.size>MAX_DRAFTS)memory.current.delete(candidate);
    try{
      const drafts=Object.keys(sessionStorage).filter(candidate=>candidate.startsWith(QUIZ_DRAFT_PREFIX)&&candidate!==key).map(candidate=>({key:candidate,draft:read(candidate)})).filter(entry=>entry.draft).sort((a,b)=>a.draft!.savedAt-b.draft!.savedAt);
      for(const old of drafts.slice(0,Math.max(0,drafts.length-MAX_DRAFTS+1)))sessionStorage.removeItem(old.key);
      sessionStorage.setItem(key,JSON.stringify(draft));
    }catch{}
  }
  return {key,ref,onChange,clear};
}
