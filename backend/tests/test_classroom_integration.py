from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models as m
from app.services.quiz_grading import GradingUnavailable

pytestmark=pytest.mark.integration

def post(client,path,body=None):
    r=client.post('/api'+path,json=body) if body is not None else client.post('/api'+path)
    assert r.status_code in (200,201),r.text
    return r.json()['data']

def login(client,name):
    return post(client,'/auth/login',dict(username=name,password='integration-password-123'))

def test_class_content_quiz_scope_saved_feedback_and_recommendations(live_client,integration_engine,monkeypatch):
    client=live_client;login(client,'teacher_demo')
    codes=client.get('/api/teacher/invitation').json()['data']
    home=client.get('/api/classroom').json()['data']
    basics=next(s for s in home['subjects'] if s['title']=='Basic programming')
    subject=post(client,'/classroom/subjects',dict(title='Basic Maths',description='Number reasoning'))
    course=post(client,f"/classroom/subjects/{subject['id']}/courses",dict(title='Fractions',content='A fraction represents a part of a whole. Equivalent fractions have the same value.'))
    foreign=post(client,'/auth/signup',dict(username='other_'+uuid4().hex[:8],password='integration-password-123',role='teacher',invite_code=codes['teacher_code']))
    assert client.post(f"/api/classroom/subjects/{subject['id']}/courses",json=dict(title='Bad',content='Not your class content.')).status_code==404
    foreign_code=client.get('/api/teacher/invitation').json()['data']['student_code']
    login(client,'teacher_demo')
    payload=dict(subject_id=basics['id'],title='Reason through new code',questions=[dict(course_id=c['id'],prompt='Explain this topic: '+c['title'],expected_answer='Teacher answer '+str(i),rubric='Explain each step.') for i,c in enumerate(basics['courses'])])
    invalid={**payload,'questions':[{**payload['questions'][0],'course_id':course['id']}]}
    assert client.post('/api/classroom/quizzes',json=invalid).status_code==422
    quiz=post(client,'/classroom/quizzes',payload)
    payload['title']='A revised quiz title'
    quiz=post(client,f"/classroom/quizzes/{quiz['id']}/update",payload)
    assert quiz['title']==payload['title']
    learner=post(client,'/auth/signup',dict(username='class_'+uuid4().hex[:8],password='integration-password-123',role='learner',invite_code=codes['student_code']))
    classroom=client.get('/api/classroom').json()['data']
    assert subject['id'] in {s['id'] for s in classroom['subjects']}
    assert not classroom['quizzes']
    assert client.get('/api/classroom/quizzes/'+quiz['id']).status_code==404
    assert client.post('/api/classroom/subjects',json=dict(title='Forbidden')).status_code==403
    login(client,'teacher_demo');post(client,f"/classroom/quizzes/{quiz['id']}/publish")
    assert client.post(f"/api/classroom/quizzes/{quiz['id']}/update",json=payload).status_code==409
    login(client,learner['username'])
    visible=client.get('/api/classroom/quizzes/'+quiz['id']).json()['data']
    assert all('expected_answer' not in q and 'rubric' not in q for q in visible['questions'])
    answers=dict(responses=[dict(question_id=q['id'],answer='An answer',reasoning='My reasoning for this answer.') for q in quiz['questions']])
    assert client.post(f"/api/classroom/quizzes/{quiz['id']}/submit",json={'responses':answers['responses'][:1]}).status_code==422
    def unavailable(_): raise GradingUnavailable('QUOTA_LIMIT')
    monkeypatch.setattr('app.services.quiz_submissions.grade_questions',unavailable)
    result=post(client,f"/classroom/quizzes/{quiz['id']}/submit",answers)
    submission=result['submissions'][0]
    assert submission['status']=='pending' and submission['responses']==answers['responses']
    assert submission['evaluation'] is None
    # A cached pending ORM row must not override another request's grading claim.
    from app.services.quiz_submissions import evaluate_submission
    from app.errors import AppError
    with Session(integration_engine,expire_on_commit=False) as stale:
        cached=stale.get(m.QuizSubmission,submission['id'])
        user=stale.get(m.User,learner['id'])
        with Session(integration_engine) as other:
            row=other.get(m.QuizSubmission,submission['id'])
            row.status='grading';row.grading_token='other-worker';row.grading_started_at=m.now();other.commit()
        assert cached.status=='pending'
        with pytest.raises(AppError) as conflict: evaluate_submission(stale,user,submission['id'])
        assert conflict.value.code=='GRADING_IN_PROGRESS'
        stale.rollback()
    with Session(integration_engine) as other:
        row=other.get(m.QuizSubmission,submission['id']);row.status='pending';row.grading_token=None;other.commit()
    assert client.post(f"/api/classroom/quizzes/{quiz['id']}/submit",json=answers).status_code==409
    def fixture_feedback(questions):
        # External transport fixture only; never used in the product.
        return {'source':'test fixture','model':'fixture','questions':[dict(question_id=q['question_id'],answer_score=score,reasoning_score=score,feedback='Check the steps.',misconception='') for q,score in zip(questions,[90,45,20])]}
    monkeypatch.setattr('app.services.quiz_submissions.grade_questions',fixture_feedback)
    result=post(client,f"/classroom/submissions/{submission['id']}/retry")
    assert result['submissions'][0]['status']=='graded'
    home=client.get('/api/classroom').json()['data']
    ordered=next(s for s in home['subjects'] if s['id']==basics['id'])['courses']
    assert [c['score'] for c in ordered]==[20,45,90]
    recommendations=client.get('/api/learner/home').json()['data']['exercises']
    assert [e['score'] for e in recommendations]==[20,45,90]
    assert result['submissions'][0]['responses']==answers['responses']
    # A different student in the same class cannot retry/read another student's result.
    post(client,'/auth/signup',dict(username='peer_'+uuid4().hex[:8],password='integration-password-123',role='learner',invite_code=codes['student_code']))
    assert client.post(f"/api/classroom/submissions/{submission['id']}/retry").status_code==404
    assert client.get('/api/classroom/quizzes/'+quiz['id']).json()['data']['submissions']==[]
    # A different class cannot see the published quiz or its results.
    post(client,'/auth/signup',dict(username='outside_'+uuid4().hex[:8],password='integration-password-123',role='learner',invite_code=foreign_code))
    assert client.get('/api/classroom/quizzes/'+quiz['id']).status_code==404
    login(client,'teacher_demo')
    result=client.get('/api/classroom/quizzes/'+quiz['id']).json()['data']
    assert len(result['submissions'])==1 and result['submissions'][0]['learner']==learner['username']
