'use client';
import { useCallback, useEffect, useState, type SetStateAction } from 'react';
import { api } from './api';

export function useResource<T>(path: string) {
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState<{path:string;revision:number;data:T|null;error:unknown;loading:boolean}>(
    {path,revision:0,data:null,error:null,loading:true});
  useEffect(() => {
    let active = true;
    api<T>(path).then(data => { if (active) setResult({path,revision,data,error:null,loading:false}); })
      .catch(error => { if (active) setResult({path,revision,data:null,error,loading:false}); });
    return () => { active = false; };
  }, [path, revision]);
  const setData = useCallback((value:SetStateAction<T|null>) => {
    setResult(previous => {
      // A late mutation for an earlier page must not replace the current page.
      if(previous.path!==path||previous.revision!==revision)return previous;
      const data=typeof value==='function'?(value as (previous:T|null)=>T|null)(previous.data):value;
      return {...previous,data,error:null,loading:false};
    });
  }, [path,revision]);
  const reload = useCallback(() => { setRevision(value => value + 1); }, []);
  const current=result.path===path&&result.revision===revision;
  return { data:current?result.data:null, setData, error:current?result.error:null, loading:!current||result.loading, reload };
}
