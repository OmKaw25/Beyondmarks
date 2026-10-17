import {DelayedCheckView} from '@/components/delayed-check-view';
export default async function CheckPage({params}:{params:Promise<{id:string}>}){const {id}=await params;return <DelayedCheckView id={id}/>;}
