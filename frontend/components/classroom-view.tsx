'use client';
import Link from 'next/link';
import {useState,type FormEvent} from 'react';
import {useRouter} from 'next/navigation';
import {useResource} from '@/lib/use-resource';
import {post} from '@/lib/api';
import type {Classroom,Subject,Quiz} from '@/lib/classroom-types';
import type {Journey} from '@/lib/types';
import {AppShell} from './site-shell';
import {Empty,ErrorPanel,Loading,PageHeading} from './primitives';

function SubjectForm({done}:{done:()=>void}){
  const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);
  async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();const form=e.currentTarget;const f=new FormData(form);setBusy(true);setError(null);try{await post('/classroom/subjects',{title:f.get('title'),description:f.get('description')});form.reset();done();}catch(err){setError(err);}finally{setBusy(false);}}
  return <details className="card"><summary>Add a subject</summary><form className="form-stack section-space" onSubmit={submit}>{error?<ErrorPanel error={error}/>:null}<label>Subject name<input name="title" required minLength={2} maxLength={120} placeholder="For example, Basic Maths"/></label><label>About this subject<textarea name="description" maxLength={2000} rows={2}/></label><button className="button" disabled={busy}>Add subject</button></form></details>;
}

function CourseForm({subject,done}:{subject:Subject;done:()=>void}){
  const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);
  async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();const form=e.currentTarget;const f=new FormData(form);setBusy(true);setError(null);try{await post(`/classroom/subjects/${subject.id}/courses`,{title:f.get('title'),content:f.get('content')});form.reset();done();}catch(err){setError(err);}finally{setBusy(false);}}
  return <details className="section-space"><summary>Add a course to {subject.title}</summary><form className="form-stack section-space" onSubmit={submit}>{error?<ErrorPanel error={error}/>:null}<label>Course / topic name<input name="title" required minLength={2} maxLength={150}/></label><label>Lesson content<textarea name="content" required minLength={10} maxLength={20000} rows={6} placeholder="Explain the topic, add examples, and suggest practice."/></label><button className="button" disabled={busy}>Save course</button></form></details>;
}

export function QuizForm({subjects,initial,done}:{subjects:Subject[];initial?:Quiz;done?:(quiz:Quiz)=>void}){
  const eligible=subjects.filter(s=>s.courses.length);const [subjectId,setSubjectId]=useState(initial?.subject_id||eligible[0]?.id||'');
  const [questions,setQuestions]=useState(initial?.questions.map((q,i)=>({key:i,course_id:q.course_id,prompt:q.prompt,expected_answer:q.expected_answer||'',rubric:q.rubric||''}))||[{key:0,course_id:'',prompt:'',expected_answer:'',rubric:''}]);
  const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);const router=useRouter();
  const subject=eligible.find(s=>s.id===subjectId);
  function change(index:number,key:string,value:string){setQuestions(items=>items.map((q,i)=>i===index?{...q,[key]:value}:q));}
  async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();setBusy(true);setError(null);const f=new FormData(e.currentTarget);try{const quiz=await post<Quiz>(initial?`/classroom/quizzes/${initial.id}/update`:'/classroom/quizzes',{subject_id:subjectId,title:f.get('title'),questions:questions.map(({course_id,prompt,expected_answer,rubric})=>({course_id,prompt,expected_answer,rubric}))});if(done)done(quiz);else router.push(`/classroom/quizzes/${quiz.id}`);}catch(err){setError(err);}finally{setBusy(false);}}
  if(!eligible.length)return <p className="muted">Add a subject and a course before creating a quiz.</p>;
  return <details className="card section-space" open={initial?true:undefined}><summary>{initial?'Edit quiz draft':'Create a quiz'}</summary><p className="section-space muted">Write fresh questions for your class. Review the draft before publishing.</p><form className="form-stack" onSubmit={submit}>
    {error?<ErrorPanel error={error}/>:null}<label>Quiz title<input name="title" required minLength={2} maxLength={150} defaultValue={initial?.title}/></label>
    <label>Quiz subject<select value={subjectId} onChange={e=>{setSubjectId(e.target.value);setQuestions(qs=>qs.map(q=>({...q,course_id:''})));}}>{eligible.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select></label>
    {questions.map((q,i)=><fieldset className="card" key={q.key}><legend>Question {i+1}</legend><div className="form-stack">
      <label>Topic for question {i+1}<select required value={q.course_id} onChange={e=>change(i,'course_id',e.target.value)}><option value="">Choose a topic</option>{subject?.courses.map(c=><option key={c.id} value={c.id}>{c.title}</option>)}</select></label>
      <label>Question {i+1} text<textarea required minLength={3} maxLength={3000} rows={3} value={q.prompt} onChange={e=>change(i,'prompt',e.target.value)}/></label>
      <label>Answer key for question {i+1}<textarea required maxLength={3000} rows={2} value={q.expected_answer} onChange={e=>change(i,'expected_answer',e.target.value)}/></label>
      <label>Reasoning guidance for question {i+1}<textarea maxLength={2000} rows={2} placeholder="What should a good explanation demonstrate?" value={q.rubric} onChange={e=>change(i,'rubric',e.target.value)}/></label>
      {questions.length>1&&<button type="button" className="text-button" onClick={()=>setQuestions(items=>items.filter((_,n)=>n!==i))}>Remove question {i+1}</button>}
    </div></fieldset>)}
    <div className="actions"><button type="button" className="button secondary" disabled={questions.length>=20||busy} onClick={()=>setQuestions(items=>[...items,{key:Math.max(...items.map(q=>q.key))+1,course_id:'',prompt:'',expected_answer:'',rubric:''}])}>Add question</button><button className="button" disabled={busy}>{busy?'Saving…':'Save quiz draft'}</button></div>
  </form></details>;
}

export function ClassroomView(){
  const [quizOffset,setQuizOffset]=useState(0);const resource=useResource<Classroom>(`/classroom?quiz_offset=${quizOffset}`);const [error,setError]=useState<unknown>(null);const [busy,setBusy]=useState('');const router=useRouter();const data=resource.data;const teacher=data?.role==='teacher';
  async function practice(id:string){setBusy(id);try{const j=await post<Journey>('/investigations/start',{exercise_id:id});router.push(j.next_url);}catch(e){setError(e);}finally{setBusy('');}}
  return <AppShell><PageHeading eyebrow="YOUR CLASSROOM" title={teacher?'Subjects, lessons, and fresh questions.':'Your next steps in learning.'}>{teacher?'Teach the topics your class needs. See how each learner reasons.':'Your teacher’s lessons and quizzes, with a learning order that responds to your work.'}</PageHeading>
    {resource.loading?<Loading/>:resource.error?<ErrorPanel error={resource.error} retry={resource.reload}/>:data&&<>
      {error?<ErrorPanel error={error}/>:null}
      {teacher&&<><SubjectForm done={resource.reload}/><QuizForm key={data.subjects.map(s=>s.id+':'+s.courses.length).join(',')} subjects={data.subjects}/></>}
      <section className="section-space"><h2>Class quizzes</h2>{data.quizzes.length?<div className="three-grid">{data.quizzes.map(q=><article className="card" key={q.id}><span className="badge">{q.status==='draft'?'Draft':q.submission_status==='graded'?'Feedback ready':q.submission_status?'Answers saved':'Ready to try'}</span><h3 className="section-space">{q.title}</h3><p className="small muted">{data.subjects.find(s=>s.id===q.subject_id)?.title}</p><Link className="button secondary" href={`/classroom/quizzes/${q.id}`}>{teacher?'Review quiz':q.submission_status?'View results':'Open quiz'}</Link></article>)}</div>:<Empty title="No quizzes yet">{teacher?'Create a quiz above when your questions are ready.':'Your teacher’s published quizzes will appear here.'}</Empty>}</section>
      {data.quizzes_page&&data.quizzes_page.total>data.quizzes_page.limit&&<div className="actions section-space"><button className="button secondary" disabled={quizOffset===0} onClick={()=>setQuizOffset(Math.max(0,quizOffset-data.quizzes_page!.limit))}>Previous quizzes</button><span className="small muted">Showing {quizOffset+1}–{quizOffset+data.quizzes.length} of {data.quizzes_page.total}</span><button className="button secondary" disabled={!data.quizzes_page.has_more} onClick={()=>setQuizOffset(data.quizzes_page!.next_offset!)}>Next quizzes</button></div>}
      <section className="section-space"><h2>{teacher?'Your subjects':'Subjects and courses'}</h2>{!data.subjects.length&&<Empty title="No class subjects yet">Your teacher’s subjects will appear here after enrollment.</Empty>}
        {data.subjects.map(s=><article className="card section-space" key={s.id}><div className="section-bar"><h2>{s.title}</h2>{!teacher&&<span className="small muted">Teacher: {s.teacher}</span>}</div><p>{s.description}</p>
          {!s.courses.length&&<p className="muted">Lessons will appear here when your teacher adds them.</p>}
          <div className="form-stack">{s.courses.map(c=><details className="card" key={c.id}><summary>{c.title}{!teacher&&c.score!==null&&<span className="badge">{c.score<60?'Recommended next':'Latest quiz'} · {c.score}%</span>}</summary>
            {!teacher&&c.score!==null&&<p className="small muted section-space">{c.score<60?'Your latest quiz suggests this topic would benefit from another look.':'This score combines answer accuracy and reasoning from your latest assessed quiz.'}</p>}
            <div className="lesson-content section-space">{c.content}</div>{!teacher&&c.exercise_id&&<button className="button secondary section-space" disabled={!!busy} onClick={()=>practice(c.exercise_id!)}>Practise this topic →</button>}
          </details>)}</div>{teacher&&<CourseForm subject={s} done={resource.reload}/>}</article>)}
      </section>
    </>}
  </AppShell>;
}
