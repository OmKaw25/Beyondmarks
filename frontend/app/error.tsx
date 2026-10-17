'use client';
import {ErrorPanel} from '@/components/primitives';
export default function ErrorPage({reset}:{reset:()=>void}){return <main id="main" className="container section-space"><ErrorPanel error={new Error('This page could not be loaded. Please try again.')} retry={reset}/></main>;}
