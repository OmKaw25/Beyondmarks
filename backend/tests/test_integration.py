from uuid import uuid4
import pytest
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from app import models as m
from app.content.catalog import catalog,uid
from app.seed import seed

pytestmark=pytest.mark.integration


def signup(client):
    send(client,'/api/auth/login',dict(username='teacher_demo',password='integration-password-123'))
    code=client.get('/api/teacher/invitation').json()['data']['student_code']
    username='test_'+uuid4().hex[:12]
    response=client.post('/api/auth/signup',json=dict(username=username,password='integration-password-123',role='learner',invite_code=code))
    assert response.status_code==201,response.text
    return response.json()['data']


def send(client,path,payload=None):
    response=client.post(path,json=payload) if payload is not None else client.post(path)
    assert response.status_code in (200,201),response.text
    return response.json()['data']


def test_student_enrollment_codes_are_distinct_reusable_and_scoped(live_client):
    client=live_client
    send(client,'/api/auth/login',dict(username='teacher_demo',password='integration-password-123'))
    parent=client.get('/api/teacher/invitation').json()['data']
    assert parent['student_code'] != parent['teacher_code']
    teacher=send(client,'/api/auth/signup',dict(username='owner_'+uuid4().hex[:10],password='integration-password-123',role='teacher',invite_code=parent['teacher_code']))
    codes=client.get('/api/teacher/invitation').json()['data']
    assert codes['teacher_id']==teacher['id']
    assert len({parent['student_code'],parent['teacher_code'],codes['student_code'],codes['teacher_code']})==4
    users=[]
    for index in range(2):
        learner=send(client,'/api/auth/signup',dict(username='enrolled_'+uuid4().hex[:10],password='integration-password-123',role='learner',invite_code=codes['student_code']))
        users.append(learner['id'])
        assert client.get('/api/teacher/invitation').status_code==403
    for role,code in [('learner',''),('learner',codes['teacher_code']),('teacher',codes['student_code'])]:
        response=client.post('/api/auth/signup',json=dict(username='invalid_'+uuid4().hex[:10],password='integration-password-123',role=role,invite_code=code))
        assert response.status_code==403
    send(client,'/api/auth/login',dict(username=teacher['username'],password='integration-password-123'))
    assert {u['id'] for u in client.get('/api/teacher/learners').json()['data']}==set(users)
    assert client.get('/api/teacher/learners/'+uid('learner_a')+'/timeline').status_code==404


def begin(client,e):
    return send(client,'/api/investigations/start',{'exercise_id':e['id']})


def reach_transfer(client,e,disagree=False):
    j=begin(client,e);base='/api/investigations/'+j['id']
    # Deliberately imperfect explanation preserves multiple competing possibilities.
    j=send(client,base+'/correction',dict(segment_ids=[e['segments'][1]['id']],broad_category='Output',specific_reason='output_format',explanation='I noticed the number but am unsure about the cause.'))
    assert j['stage']=='diagnosis'
    if disagree:
        j=send(client,base+'/challenge',dict(alternative_hypothesis_id=e['hypotheses'][1]['id'],reason='I may have read the task too quickly.'))
        assert j['challenge']
    j=send(client,base+'/select-follow-up')
    if j['stage']=='follow-up':
        assert j['selection']['rationale']
        assert 'correct_choice' not in j['followup']
        j=send(client,base+'/follow-up',{'answer':e['followups'][0]['correct_choice']})
    assert j['stage']=='support'
    support=next(s for s in e['support'] if s['id']==j['support']['id'])
    j=send(client,base+'/support',{'support_id':support['id'],'answer':support['correct_choice']})
    assert j['stage']=='support' and j['support_completed'] and j['result']['feedback']
    j=send(client,base+'/continue-support',{'support_id':support['id']})
    assert j['stage']=='transfer'
    return j,base


def reach_verification(client,e,disagree=False):
    j,base=reach_transfer(client,e,disagree)
    task=next(t for t in e['transfer'] if t['id']==j['task']['id'])
    j=send(client,base+'/transfer',dict(task_id=task['id'],answer=task['interaction_json']['correct_answer'],explanation='I tracked the value after each operation.',reasoning_tag='trace'))
    assert j['stage']=='independent'
    assert 'expected_output' not in j['task'] and 'correct_tag' not in j['task']
    return j,base


def test_full_journey_and_immutable_submissions(live_client):
    client=live_client;signup(client);e=catalog()[0]
    j,base=reach_verification(client,e,disagree=True)
    task=next(t for t in e['independent'] if t['id']==j['task']['id'])
    j=send(client,base+'/independent',dict(task_id=task['id'],answer=task['expected_output'],explanation='Assignment updates only the selected variable.',reasoning_tag='trace'))
    assert j['stage']=='reflection' and j['status']=='active'
    for key in ('exercise','support','assessment','adaptation','result','selection'):
        assert j[key] is None
    task=next(t for t in e['reflection'] if t['id']==j['task']['id'])
    j=send(client,base+'/reflection',dict(task_id=task['id'],answer=task['interaction_json']['correct_answer'],explanation='This value makes the original and its copy differ.',reasoning_tag='trace'))
    assert j['stage']=='retention' and j['result']['passed']
    assert client.post(base+'/reflection',json=dict(task_id=task['id'],answer='0',explanation='Change the old answer',reasoning_tag='guess')).status_code==409
    assert client.post(base+'/independent',json=dict(task_id=task['id'],answer='0',explanation='Change the old answer',reasoning_tag='guess')).status_code==409
    assert client.get(base).json()['data']['result']['passed']
    assert client.get('/api/retention').json()['data']==[]


def stored(engine, model, id):
    with Session(engine) as db:
        row=db.get(model,id)
        return {column.name:getattr(row,column.name) for column in model.__table__.columns}


def test_independent_failure_changes_support_and_task(live_client,integration_engine):
    client=live_client;signup(client);e=catalog()[2]
    j,base=reach_verification(client,e)
    old_task=j['task']['id']
    j=send(client,base+'/independent',dict(task_id=j['task']['id'],answer='wrong',explanation='I guessed based on a familiar pattern.',reasoning_tag='guess'))
    assert j['stage']=='support'
    assert j['adaptation']['old'] and j['adaptation']['new']
    support=stored(integration_engine,m.SupportModule,j['support']['id'])
    j=send(client,base+'/support',{'support_id':support['id'],'answer':support['correct_choice']})
    j=send(client,base+'/continue-support',{'support_id':support['id']})
    assert j['stage']=='independent' and j['task']['id']!=old_task


def test_repeated_failures_get_new_content_and_preserve_questions_on_reload(live_client, integration_engine):
    client=live_client; signup(client); e=catalog()[0]
    j,base=reach_verification(client,e)
    seen_support={e['support'][0]['worked_example']}; seen_tasks=set()
    for _ in range(5):
        old_task=j['task']['id']; seen_tasks.add(j['task']['code'])
        j=send(client,base+'/independent',dict(task_id=old_task,answer='wrong',explanation='I need more practice.',reasoning_tag='guess'))
        assert j['stage']=='support'
        assert j['support']['worked_example'] not in seen_support
        seen_support.add(j['support']['worked_example'])
        assert client.get(base).json()['data']['support']==j['support']
        assert not j['support_completed']
        with Session(integration_engine) as db:
            support=db.get(m.SupportModule,j['support']['id'])
            correct=support.correct_choice
        support_id=j['support']['id']
        send(client,base+'/support',dict(support_id=support_id,answer=correct))
        j=send(client,base+'/continue-support',dict(support_id=support_id))
        assert j['stage']=='independent' and j['status']=='active'
        assert j['task']['code'] not in seen_tasks
        assert j['task']['interaction']['difficulty']=='Challenge'
        assert client.get(base).json()['data']['task']==j['task']
        assert client.post(base+'/independent',json=dict(task_id=old_task,answer='wrong',explanation='Stale tab response.',reasoning_tag='guess')).status_code==409


def test_wrong_learn_prediction_requires_fresh_practice(live_client):
    client=live_client; signup(client); e=catalog()[0]
    j=begin(client,e); base='/api/investigations/'+j['id']
    send(client,base+'/correction',dict(segment_ids=[e['segments'][1]['id']],broad_category=e['broad'],specific_reason=e['reason'],explanation='Assignment copies the current value.'))
    j=send(client,base+'/select-follow-up')
    if j['stage']=='follow-up':
        j=send(client,base+'/follow-up',dict(answer=e['followups'][0]['correct_choice']))
    original=j['support']
    support=next(s for s in e['support'] if s['id']==original['id'])
    wrong=next(c['value'] for c in support['choices'] if c['value']!=support['correct_choice'])
    send(client,base+'/support',dict(support_id=original['id'],answer=wrong))
    j=send(client,base+'/continue-support',dict(support_id=original['id']))
    assert j['stage']=='support' and not j['support_completed']
    assert j['support']['worked_example']!=original['worked_example']
    assert client.post(base+'/support',json=dict(support_id=original['id'],answer=wrong)).status_code==409


def test_transfer_failure_retries_transfer_before_independent_work(live_client,integration_engine):
    client=live_client; signup(client); e=catalog()[2]
    j,base=reach_transfer(client,e)
    original=j['task']
    j=send(client,base+'/transfer',dict(task_id=original['id'],answer='wrong',explanation='I included the stop value.',reasoning_tag='guess'))
    assert j['stage']=='support' and j['status']=='active'
    support=stored(integration_engine,m.SupportModule,j['support']['id'])
    send(client,base+'/support',dict(support_id=support['id'],answer=support['correct_choice']))
    j=send(client,base+'/continue-support',dict(support_id=support['id']))
    assert j['stage']=='transfer' and j['task']['id']!=original['id']
    task=stored(integration_engine,m.TransferTask,j['task']['id'])
    j=send(client,base+'/transfer',dict(task_id=task['id'],answer=task['interaction_json']['correct_answer'],explanation='The stop is excluded.',reasoning_tag=task['correct_tag']))
    assert j['stage']=='independent'


def test_generated_content_is_shared_between_students(live_client,integration_engine):
    client=live_client; e=catalog()[0]; support_ids=[]; task_ids=[]
    for _ in range(2):
        signup(client); j,base=reach_verification(client,e)
        j=send(client,base+'/independent',dict(task_id=j['task']['id'],answer='wrong',explanation='I need a new example.',reasoning_tag='guess'))
        support_ids.append(j['support']['id'])
        with Session(integration_engine) as db:
            attempt=db.get(m.Attempt,j['id'])
            task_ids.append(attempt.state['independent_id'])
    assert support_ids[0]==support_ids[1]
    assert task_ids[0]==task_ids[1]


def test_reflection_failure_requires_fresh_challenge_after_support(live_client,integration_engine):
    client=live_client;signup(client);e=catalog()[1]
    j,base=reach_verification(client,e)
    task=next(t for t in e['independent'] if t['id']==j['task']['id'])
    j=send(client,base+'/independent',dict(task_id=task['id'],answer=task['expected_output'],explanation='I used the updated value for the next condition.',reasoning_tag='trace'))
    assert j['stage']=='reflection'
    old_task=j['task']['id']
    j=send(client,base+'/reflection',dict(task_id=old_task,answer='wrong',explanation='I guessed at the boundary.',reasoning_tag='guess'))
    assert j['stage']=='support' and j['status']=='active' and j['adaptation']
    support=stored(integration_engine,m.SupportModule,j['support']['id'])
    send(client,base+'/support',dict(support_id=support['id'],answer=support['correct_choice']))
    j=send(client,base+'/continue-support',dict(support_id=support['id']))
    assert j['stage']=='reflection' and j['task']['id']!=old_task
    assert j['result'] is None and j['adaptation'] is None
    task=stored(integration_engine,m.IndependentTask,j['task']['id'])
    assert client.post(base+'/reflection',json=dict(task_id=old_task,answer='10',explanation='A stale response.',reasoning_tag='trace')).status_code==409
    j=send(client,base+'/reflection',dict(task_id=task['id'],answer=task['interaction_json']['correct_answer'],explanation='At equality, only the inclusive comparison is true.',reasoning_tag='trace'))
    assert j['stage']=='retention' and j['status']=='complete'


def test_adapted_support_feedback_is_separate_from_independent_check(live_client,integration_engine):
    client=live_client;signup(client);e=catalog()[1]
    j,base=reach_verification(client,e)
    j=send(client,base+'/independent',dict(task_id=j['task']['id'],answer='wrong',explanation='I guessed the result.',reasoning_tag='guess'))
    support=stored(integration_engine,m.SupportModule,j['support']['id'])
    wrong=next(c['value'] for c in support['choices_json'] if c['value']!=support['correct_choice'])
    j=send(client,base+'/support',{'support_id':support['id'],'answer':wrong})
    assert j['stage']=='support' and j['support_completed']
    assert j['result']['feedback']==support['feedback_incorrect']
    j=send(client,base+'/continue-support',{'support_id':support['id']})
    assert j['stage']=='support' and j['support']['id']!=support['id']
    fresh=stored(integration_engine,m.SupportModule,j['support']['id'])
    send(client,base+'/support',dict(support_id=fresh['id'],answer=fresh['correct_choice']))
    j=send(client,base+'/continue-support',dict(support_id=fresh['id']))
    assert j['stage']=='independent'
    for key in ('result','support','assessment','adaptation','selection','exercise'):
        assert j[key] is None, f'{key} exposes earlier teaching during independent work'
    assert support['feedback_incorrect'] not in str(j)


def test_ownership_permissions_and_logout(live_client):
    client=live_client;signup(client);attempt=begin(client,catalog()[0])
    assert client.get('/api/teacher/learners').status_code==403
    send(client,'/api/auth/logout')
    assert client.get('/api/auth/me').status_code==401
    signup(client)
    assert client.get('/api/investigations/'+attempt['id']).status_code==404
    assert client.post('/api/auth/signup',json=dict(username='unauthorized_teacher',password='integration-password-123',role='teacher',invite_code='invalid')).status_code==403


def test_synthetic_retention_and_teacher_scope(live_client):
    client=live_client
    send(client,'/api/auth/login',{'username':'learner_a','password':'integration-password-123'})
    checks=client.get('/api/retention').json()['data']
    assert {c['outcome'] for c in checks}=={'PASS','FAIL'}
    assert all(c['is_synthetic'] for c in checks)
    failed=next(c for c in checks if c['outcome']=='FAIL')
    j=send(client,f"/api/retention/{failed['id']}/adapt")
    assert j['is_synthetic'] and j['adaptation'] and j['stage']=='support'
    assert send(client,f"/api/retention/{failed['id']}/adapt")['id']==j['id']
    send(client,'/api/auth/login',{'username':'teacher_demo','password':'integration-password-123'})
    assert {uid(n) for n in ['learner_a','learner_b','learner_c']} <= {u['id'] for u in client.get('/api/teacher/learners').json()['data']}
    response=client.get('/api/teacher/learners/'+uid('learner_a')+'/timeline')
    assert response.status_code==200 and response.json()['data']['events']
    events=client.get('/api/teacher/learners/'+uid('learner_c')+'/timeline').json()['data']['events']
    disagreement=next(e for e in events if e['kind']=='Learner disagreement')['details']
    assert disagreement['system_hypothesis_label'] and disagreement['alternative_hypothesis_label']
    assert client.get('/api/teacher/learners/'+str(uuid4())+'/timeline').status_code==404


def test_seed_idempotence_and_rls(integration_engine):
    with Session(integration_engine) as db:
        before={table:db.scalar(select(func.count()).select_from(model)) for table,model in [('users',m.User),('checks',m.RetentionCheck),('rules',m.EvidenceRule)]}
        seed(db,'integration-password-123')
        after={table:db.scalar(select(func.count()).select_from(model)) for table,model in [('users',m.User),('checks',m.RetentionCheck),('rules',m.EvidenceRule)]}
        assert before==after
        protected=db.execute(text("select relname,relrowsecurity from pg_class where relnamespace=current_schema()::regnamespace and relkind='r'")).all()
        assert len(protected)==len(m.Base.metadata.tables) and all(enabled for _,enabled in protected)


def test_stale_submissions_cannot_complete_later_adaptation(live_client,integration_engine):
    client=live_client;signup(client);e=catalog()[0]
    j,base=reach_verification(client,e)
    original_task=j['task']['id']
    j=send(client,base+'/independent',dict(task_id=original_task,answer='wrong',explanation='I guessed.',reasoning_tag='guess'))
    current_support=j['support']['id']
    old_support=next(s['id'] for s in e['support'] if s['id']!=current_support)
    stale=client.post(base+'/support',json=dict(support_id=old_support,answer='4'))
    assert stale.status_code==409
    assert stale.json()['error']['code']=='STALE_SUPPORT'
    support=stored(integration_engine,m.SupportModule,current_support)
    send(client,base+'/support',dict(support_id=current_support,answer=support['correct_choice']))
    send(client,base+'/continue-support',dict(support_id=current_support))
    stale=client.post(base+'/independent',json=dict(task_id=original_task,answer='6',explanation='An old response.',reasoning_tag='trace'))
    assert stale.status_code==409
    assert stale.json()['error']['code']=='STALE_TASK'
    assert client.get(base).json()['data']['stage']=='independent'


def test_concurrent_starts_resume_one_investigation(live_client, integration_engine):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Barrier
    from app.services.journey_service import start

    user=signup(live_client);exercise=catalog()[0];entered=Barrier(3)
    def start_once():
        with Session(integration_engine,expire_on_commit=False) as db:
            learner=db.get(m.User,user['id'])
            entered.wait(timeout=5)
            result=start(db,learner,exercise['id'])
            db.commit()
            return result['id']

    with ThreadPoolExecutor(max_workers=2) as pool:
        with Session(integration_engine) as blocker:
            blocker.scalar(select(m.User).where(m.User.id==user['id']).with_for_update())
            first=pool.submit(start_once)
            second=pool.submit(start_once)
            entered.wait(timeout=5)
            try:
                # Starting must wait for the learner lock, not check/insert past it.
                with pytest.raises(TimeoutError):first.result(timeout=0.5)
                with pytest.raises(TimeoutError):second.result(timeout=0.5)
            finally:
                blocker.rollback()
        assert first.result(timeout=15)==second.result(timeout=15)
    with Session(integration_engine) as db:
        assert db.scalar(select(func.count()).select_from(m.Attempt).where(m.Attempt.learner_id==user['id']))==1


def test_teacher_signup_login_assignment_and_role_isolation(live_client,integration_engine):
    client=live_client
    learner=signup(client)
    assert client.get('/api/teacher/invitation').status_code==403
    send(client,'/api/auth/logout')
    send(client,'/api/auth/login',dict(username='teacher_demo',password='integration-password-123'))
    invite=client.get('/api/teacher/invitation').json()['data']['code']
    send(client,'/api/auth/logout')
    username='teacher_'+uuid4().hex[:10]
    teacher=send(client,'/api/auth/signup',dict(username=username,password='integration-password-123',role='teacher',invite_code=invite))
    own_code=client.get('/api/teacher/invitation').json()['data']['code']
    assert own_code!=invite
    assert client.get('/api/teacher/invitation').json()['data']['code']==own_code
    assert teacher['role']=='teacher'
    assert client.get('/api/learner/home').status_code==403
    assert client.get('/api/teacher/learners').json()['data']==[]
    assert client.get('/api/teacher/learners/'+learner['id']+'/timeline').status_code==404
    with Session(integration_engine) as db:
        db.add(m.TeacherAssignment(teacher_id=teacher['id'],learner_id=learner['id']))
        db.commit()
    assigned=client.get('/api/teacher/learners').json()['data']
    assert [row['id'] for row in assigned]==[learner['id']]
    assert client.get('/api/teacher/learners/'+learner['id']+'/timeline').status_code==200
    send(client,'/api/auth/logout')
    logged_in=send(client,'/api/auth/login',dict(username=username.upper(),password='integration-password-123'))
    assert logged_in['role']=='teacher' and logged_in['id']==teacher['id']
    assert client.post('/api/auth/login',json=dict(username=username,password='integration-password-123',role='learner')).status_code==422
    send(client,'/api/auth/logout')
    logged_in=send(client,'/api/auth/login',dict(username=learner['username'],password='integration-password-123'))
    assert logged_in['role']=='learner'
    assert client.get('/api/teacher/learners').status_code==403
    # The same inviter code can register another teacher without being consumed.
    other=send(client,'/api/auth/signup',dict(username='teacher_'+uuid4().hex[:10],password='integration-password-123',role='teacher',invite_code=invite))
    assert other['role']=='teacher' and other['id']!=teacher['id']
    assert client.get('/api/teacher/invitation').json()['data']['code'] not in (invite,own_code)
    assert client.get('/api/teacher/learners').json()['data']==[]


def test_auth_rejects_duplicate_credentials_and_expired_stored_session(live_client,integration_engine):
    from datetime import timedelta
    client=live_client;user=signup(client)
    with Session(integration_engine) as db:
        student_code=db.scalar(select(m.TeacherInviteCode).where(m.TeacherInviteCode.teacher_id==uid('teacher_demo'))).student_code
    cookie=client.cookies.get('bm_session')
    assert client.post('/api/auth/signup',json=dict(username=user['username'].upper(),password='integration-password-123',invite_code=student_code)).status_code==409
    assert client.post('/api/auth/login',json=dict(username=user['username'],password='wrong-password')).status_code==401
    with Session(integration_engine) as db:
        session=db.scalar(select(m.AuthSession).where(m.AuthSession.user_id==user['id']))
        session.expires_at=m.now()-timedelta(seconds=1)
        db.commit()
    assert cookie and client.get('/api/auth/me').status_code==401


def test_investigation_rejects_foreign_content_and_repeated_correction(live_client):
    client=live_client;signup(client);e=catalog()[0];foreign=catalog()[1]
    j=begin(client,e);base='/api/investigations/'+j['id']
    payload=dict(segment_ids=[foreign['segments'][0]['id']],broad_category='Output',specific_reason='output_format',explanation='I examined the explanation.')
    assert client.post(base+'/correction',json=payload).status_code==422
    payload['segment_ids']=[e['segments'][1]['id']]
    payload['specific_reason']='not-an-offered-reason'
    assert client.post(base+'/correction',json=payload).status_code==422
    payload['specific_reason']='output_format'
    send(client,base+'/correction',payload)
    assert client.post(base+'/correction',json=payload).status_code==409
    assert client.post(base+'/challenge',json=dict(alternative_hypothesis_id=foreign['hypotheses'][0]['id'],reason='Wrong exercise')).status_code==422
