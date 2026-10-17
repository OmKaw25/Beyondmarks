import Link from 'next/link';
import { ThemeToggle } from '@/components/site-shell';

export default function Landing() {
  return <div className="landing-page">
    <header className="auth-nav landing-nav">
      <Link href="/" aria-label="Beyond Marks home">Beyond Marks</Link>
      <div className="actions"><Link className="text-link" href="/login">Sign in</Link><ThemeToggle/></div>
    </header>
    <main id="main" className="landing-main">
      <section className="landing-intro" aria-labelledby="landing-title">
        <div className="auth-emblem" aria-hidden="true">bm</div>
        <h1 id="landing-title">Understand more.<br/><em>Go beyond marks.</em></h1>
        <p className="landing-description">Explore your reasoning, find the support you need, and try it on your own.</p>
        <Link className="button landing-start" href="/signup">Start learning <span aria-hidden="true">↗</span></Link>
        <p className="landing-subjects">Variables · Conditions · Loops</p>
      </section>
      <ol className="landing-steps" aria-label="Your learning journey">
        {[
          ['Explore', 'Look beyond the answer.'],
          ['Reflect', 'Consider another explanation.'],
          ['Practise', 'Get support that fits.'],
          ['Apply', 'Try it independently.'],
        ].map(([title,description],index)=><li key={title}>
          <span className="landing-step-number" aria-hidden="true">{index+1}</span>
          <h2>{title}</h2><p>{description}</p>
        </li>)}
      </ol>
    </main>
    <footer className="landing-footer">Learning comes first.</footer>
  </div>;
}
