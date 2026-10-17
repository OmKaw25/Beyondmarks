'use client';
import { useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { post } from '@/lib/api';
import type { User } from '@/lib/types';
import { ErrorPanel } from './primitives';
import { ThemeToggle } from './site-shell';

export function AuthForm({ signup = false }: { signup?: boolean }) {
  const [role,setRole] = useState('learner'); const [busy,setBusy] = useState(false); const [error,setError] = useState<unknown>(null); const router = useRouter();
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return;
    const fields = new FormData(event.currentTarget); const password = String(fields.get('password'));
    if (signup && password !== fields.get('confirm')) { setError(new Error('Your passwords do not match.')); return; }
    if (new TextEncoder().encode(password).length > 72) { setError(new Error('Use a password of at most 72 UTF-8 bytes.')); return; }
    setBusy(true); setError(null);
    try { const user = await post<User>(signup ? '/auth/signup' : '/auth/login', { username: fields.get('username'), password, ...(signup ? { role, invite_code: fields.get('invite') || '' } : {}) }); router.push(user.role === 'teacher' ? '/teacher' : '/learner'); }
    catch (e) { setError(e); } finally { setBusy(false); }
  }
  return <div className="auth-page">
    <header className="auth-nav"><Link href="/">Beyond Marks</Link><ThemeToggle/></header>
    <main id="main" className="auth-center">
      <section className="auth-neu" aria-labelledby="auth-title">
        <div className="auth-emblem" aria-hidden="true">bm</div>
        <h1 id="auth-title">{signup ? 'Create an account' : 'Welcome back'}</h1>
        <p className="auth-caption">{signup ? 'A little curiosity starts here.' : 'Sign in to your workspace.'}</p>
        {error ? <ErrorPanel error={error}/> : null}
        <form onSubmit={submit} className="form-stack">
          <label>Username<input name="username" placeholder="Your username" required minLength={3} maxLength={32} pattern="[A-Za-z0-9_]+" autoComplete="username" aria-describedby={signup?'username-help':undefined}/></label>
          {signup && <span className="small muted" id="username-help">3–32 letters, numbers, or underscores.</span>}
          <label>Password<input name="password" placeholder="Your password" type="password" required minLength={signup ? 10 : 1} maxLength={72} autoComplete={signup ? 'new-password' : 'current-password'} aria-describedby={signup?'password-help':undefined}/></label>
          {signup && <>
            <span className="small muted" id="password-help">10+ characters; at most 72 UTF-8 bytes.</span>
            <label>Confirm password<input name="confirm" type="password" required autoComplete="new-password"/></label>
            <label>Account type<select value={role} onChange={e => setRole(e.target.value)}><option value="learner">Learner</option><option value="teacher">Teacher / mentor</option></select></label>
            <label>{role === 'teacher'?'Teacher referral code':'Student enrollment code'}<input key={role} name="invite" required autoComplete="off" maxLength={200} aria-describedby="invite-help"/><span className="small muted" id="invite-help">{role==='teacher'?'Use another teacher’s referral code to create your own class.':'Get this code from your teacher to join their class.'}</span></label>
          </>}
          <button className="button full auth-submit" disabled={busy} type="submit">{busy ? 'Please wait…' : signup ? 'Create account' : 'Sign in'}</button>
        </form>
        <p className="auth-bottom">{signup ? 'Already registered?' : 'New here?'} <Link href={signup ? '/login' : '/signup'}>{signup ? 'Sign in' : 'Create an account'}</Link></p>
      </section>
    </main>
  </div>;
}
