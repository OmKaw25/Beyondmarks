'use client';
import { useCallback, useEffect, useState } from 'react';
import { api } from './api';

export function useResource<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    api<T>(path).then(value => { if (active) { setData(value); setError(null); } })
      .catch(reason => { if (active) setError(reason); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [path, revision]);
  const reload = useCallback(() => { setLoading(true); setError(null); setRevision(value => value + 1); }, []);
  return { data, setData, error, loading, reload };
}
