'use client';

import {useCallback,useEffect,useRef,type FormEvent} from 'react';
import type {Journey} from './types';
import {QUIZ_DRAFT_PREFIX} from './use-quiz-draft';

const PREFIX='bm-draft:';
const MAX_DRAFTS=20;
const MAX_AGE=24*60*60*1000;
type Values=Record<string,string[]>;
type Draft={savedAt:number;values:Values};
const fields=new Set(['segment','category','reason','explanation','confidence','context','context_note','alternative','answer','answer_0','answer_1']);

export function journeyDraftKey(j:Journey) {
  const item=j.stage==='investigate'?j.exercise?.id:j.stage==='follow-up'?j.followup?.id:j.stage==='support'?j.support?.id:j.task?.id;
  return `${PREFIX}${j.id}:${j.stage}:${item||'perspective'}`;
}

export function clearFormDraft(key:string) {try{sessionStorage.removeItem(key);}catch{}}
export function clearAllFormDrafts() {
  try {for(const key of Object.keys(sessionStorage))if(key.startsWith(PREFIX)||key.startsWith(QUIZ_DRAFT_PREFIX))sessionStorage.removeItem(key);}catch{}
}

function readDraft(key:string):Draft|null {
  try {
    const raw=sessionStorage.getItem(key);if(!raw)return null;
    const draft=JSON.parse(raw) as Draft;
    if(!draft||!Number.isFinite(draft.savedAt)||Date.now()-draft.savedAt>MAX_AGE||!draft.values||typeof draft.values!=='object') {clearFormDraft(key);return null;}
    for(const [name,values] of Object.entries(draft.values)) {
      if(!fields.has(name)||!Array.isArray(values)||values.length>50||values.some(value=>typeof value!=='string'||value.length>2000))return null;
    }
    return draft;
  }catch{return null;}
}

/** Unsubmitted work only, scoped to a server-authorized attempt and task.
 * Storage failures must never prevent learning or claim that work was submitted.
 */
export function useFormDraft(key:string,onRestore?:(values:Values)=>void) {
  const restoreCallback=useRef(onRestore);
  useEffect(()=>{restoreCallback.current=onRestore;},[onRestore]);
  const frame=useRef<number|null>(null);
  useEffect(()=>()=>{if(frame.current!==null)cancelAnimationFrame(frame.current);},[]);
  const ref=useCallback((form:HTMLFormElement|null)=>{
    if(frame.current!==null)cancelAnimationFrame(frame.current);
    if(!form)return;
    const draft=readDraft(key);if(!draft)return;
    restoreCallback.current?.(draft.values);
    // Restore after React renders any dependent reason options for the saved category.
    frame.current=requestAnimationFrame(()=>{
      for(const element of Array.from(form.elements)) {
        if(!(element instanceof HTMLInputElement||element instanceof HTMLSelectElement||element instanceof HTMLTextAreaElement))continue;
        const values=draft.values[element.name];if(!values)continue;
        if(element instanceof HTMLInputElement&&(element.type==='radio'||element.type==='checkbox'))element.checked=values.includes(element.value);
        else element.value=values[0]||'';
      }
    });
  },[key]);
  function onChange(event:FormEvent<HTMLFormElement>) {
    const values:Values={};
    for(const [name,value] of new FormData(event.currentTarget)) {
      if(fields.has(name)&&typeof value==='string')(values[name]??=[]).push(value.slice(0,2000));
    }
    try {
      const keys=Object.keys(sessionStorage).filter(candidate=>candidate.startsWith(PREFIX)&&candidate!==key);
      const drafts=keys.map(candidate=>({key:candidate,draft:readDraft(candidate)})).filter(entry=>entry.draft).sort((a,b)=>a.draft!.savedAt-b.draft!.savedAt);
      for(const entry of drafts.slice(0,Math.max(0,drafts.length-MAX_DRAFTS+1)))sessionStorage.removeItem(entry.key);
      sessionStorage.setItem(key,JSON.stringify({savedAt:Date.now(),values}));
    }catch{}
  }
  return {ref,onChange};
}
