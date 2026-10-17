'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState, type ReactNode } from 'react';
import { post } from '@/lib/api';
import {clearAllFormDrafts} from '@/lib/use-form-draft';
import { useResource } from '@/lib/use-resource';
import type { User } from '@/lib/types';
import { ErrorPanel } from './primitives';

export function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => { const id = requestAnimationFrame(() => setDark(document.documentElement.dataset.theme === 'dark')); return () => cancelAnimationFrame(id); }, []);
  function toggle() { const next = !dark; setDark(next); document.documentElement.dataset.theme = next ? 'dark' : 'light'; try { localStorage.setItem('bm-theme', next ? 'dark' : 'light'); } catch {} }
  return <button className="icon-button" aria-label={`Switch to ${dark ? 'light' : 'dark'} theme`} onClick={toggle}>{dark ? '☀' : '☾'}</button>;
}

export function Brand({href="/"}:{href?:string}) { return <Link className="brand" href={href} aria-label={href==="/"?"Beyond Marks home":"Beyond Marks dashboard"}><span className="brand-mark" aria-hidden="true">b<span>m</span></span><span>Beyond Marks<span className="brand-sub">UNDERSTANDING COMES FIRST</span></span></Link>; }
export function PublicHeader() { return <header className="public-header container"><Brand/><div className="actions"><ThemeToggle/><Link href="/login" className="text-link">Sign in</Link></div></header>; }

export function AppShell({ children }: { children: ReactNode }) {
  const path = usePathname(); const router = useRouter(); const auth = useResource<User>('/auth/me');
  const [menu, setMenu] = useState(false); const [error, setError] = useState<unknown>(null);
  const isTeacher = auth.data?.role === 'teacher';
  async function logout() { try { await post('/auth/logout'); clearAllFormDrafts(); router.push('/login'); } catch (e) { setError(e); } }
  return <div className="app-layout"><aside className={`sidebar ${menu ? 'open' : ''}`}><Brand href={isTeacher?'/teacher':'/learner'}/><button className="mobile-menu button secondary" onClick={() => setMenu(!menu)} aria-expanded={menu}>Workspace menu</button><nav aria-label="Workspace navigation"><p className="nav-label">YOUR WORKSPACE</p>{!isTeacher && <Link className={path==='/learner' ? 'active' : ''} href="/learner">◎ <span>My learning</span></Link>}{isTeacher && <Link className={path.startsWith('/teacher') ? 'active' : ''} href="/teacher">▤ <span>Learner evidence</span></Link>}<Link className={path.startsWith('/classroom') ? 'active' : ''} href="/classroom"><span>Subjects &amp; quizzes</span></Link>{!isTeacher && <Link className={path.startsWith('/retention') ? 'active' : ''} href="/retention"><span>Learning over time</span></Link>}<Link href="/">↗ <span>About Beyond Marks</span></Link></nav><div className="sidebar-note"><span className="eyebrow">A different kind of progress</span><p>Understand the reasoning.<br/>Find a useful next step.<br/>See what stays with you.</p></div></aside><div className="app-main"><header className="workspace-header"><span className="small muted">{isTeacher ? 'Teacher workspace' : 'Learning workspace'}</span><div className="actions"><ThemeToggle/>{auth.data ? <><span className="user-pill">{auth.data.username}</span><button className="text-button" onClick={logout}>Sign out</button></> : <Link href="/login">Sign in</Link>}</div></header><main id="main" className="workspace-content">{error ? <ErrorPanel error={error}/> : null}{children}</main><footer className="workspace-footer">Beyond Marks · Evidence before assumptions.</footer></div></div>;
}
