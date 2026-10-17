import {notFound} from 'next/navigation';
import {JourneyView} from '@/components/journey-view';
export default async function JourneyPage({params}:{params:Promise<{stage:string;id:string}>}){const {stage,id}=await params;if(!['investigate','diagnosis','follow-up','support','transfer','independent','reflection','retention'].includes(stage))notFound();return <JourneyView id={id} stage={stage}/>;}
