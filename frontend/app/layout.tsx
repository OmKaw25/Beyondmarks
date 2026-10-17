import type { Metadata } from 'next';
import '@/styles/globals.css';
export const metadata: Metadata = { title: { default: 'Beyond Marks — Understanding comes first', template: '%s · Beyond Marks' }, description: 'Look beyond the answer. Explore your reasoning, find the right support, and see what you can apply independently.' };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{ __html: `try{document.documentElement.dataset.theme=localStorage.getItem('bm-theme')||'light'}catch(e){}` }}/></head><body><a className="skip-link" href="#main">Skip to content</a>{children}</body></html>; }
