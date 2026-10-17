import Link from 'next/link';
import {PublicHeader} from '@/components/site-shell';
export default function NotFound(){return <><PublicHeader/><main id="main" className="container empty"><h1>This page isn’t part of your journey.</h1><p>Return to your workspace to find your next step.</p><Link className="button" href="/learner">My learning →</Link></main></>;}
