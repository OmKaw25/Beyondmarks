import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models as m
from app.content.catalog import uid

pytestmark = pytest.mark.integration


def test_roster_pagination_search_and_assignment_scope(live_client, integration_engine):
    with Session(integration_engine) as db:
        teacher = db.get(m.User, uid('teacher_demo'))
        for name in ['roster_alpha', 'roster_beta', 'roster_literal_one']:
            user = m.User(username=name, password_hash=teacher.password_hash, role='learner')
            db.add(user); db.flush()
            db.add(m.TeacherAssignment(teacher_id=teacher.id, learner_id=user.id))
        outsider = m.User(username='roster_outside', password_hash=teacher.password_hash, role='learner')
        db.add(outsider); db.commit()
    assert live_client.post('/api/auth/login', json={'username':'teacher_demo','password':'integration-password-123'}).status_code == 200
    first = live_client.get('/api/teacher/roster?search=roster_&limit=2')
    assert first.status_code == 200
    first = first.json()['data']
    assert first['page']['total'] == 3 and first['page']['has_more']
    second = live_client.get('/api/teacher/roster?search=roster_&limit=2&offset=2').json()['data']
    assert len(second['learners']) == 1 and not second['page']['has_more']
    assert {u['username'] for u in first['learners'] + second['learners']} == {'roster_alpha','roster_beta','roster_literal_one'}
    exact = live_client.get('/api/teacher/roster?search=ROSTER_ALPHA').json()['data']
    assert [u['username'] for u in exact['learners']] == ['roster_alpha']
    assert live_client.get('/api/teacher/roster?search=%25').json()['data']['page']['total'] == 0
    assert live_client.get('/api/teacher/roster?limit=51').status_code == 422
    assert live_client.get('/api/teacher/roster?offset=-1').status_code == 422
    assert live_client.get('/api/teacher/roster?search='+'x'*33).status_code == 422
    live_client.post('/api/auth/login', json={'username':'learner_a','password':'integration-password-123'})
    assert live_client.get('/api/teacher/roster').status_code == 403


def test_roster_can_hide_demonstration_accounts(live_client):
    live_client.post('/api/auth/login', json={'username':'teacher_demo','password':'integration-password-123'})
    shown = live_client.get('/api/teacher/roster?search=learner_&include_samples=true').json()['data']
    assert shown['page']['total'] >= 3
    hidden = live_client.get('/api/teacher/roster?search=learner_&include_samples=false').json()['data']
    assert hidden['learners'] == [] and hidden['page']['total'] == 0


def test_roster_defaults_exclude_samples_and_disabled_accounts(live_client, integration_engine):
    with Session(integration_engine) as db:
        teacher = db.get(m.User, uid('teacher_demo'))
        for name, flags in [
            ('scope_real', {}),
            ('scope_sample', {'is_synthetic': True}),
            ('scope_demo', {'data_origin': 'demo'}),
            ('scope_disabled', {'active': False}),
        ]:
            user = m.User(username=name, password_hash=teacher.password_hash, role='learner', **flags)
            db.add(user); db.flush()
            db.add(m.TeacherAssignment(teacher_id=teacher.id, learner_id=user.id))
        db.commit()
    live_client.post('/api/auth/login', json={'username':'teacher_demo','password':'integration-password-123'})
    for endpoint in ('roster', 'learners'):
        response = live_client.get(f'/api/teacher/{endpoint}?search=scope_').json()
        learners = response['data']['learners'] if endpoint == 'roster' else response['data']
        assert [u['username'] for u in learners] == ['scope_real']
        response = live_client.get(f'/api/teacher/{endpoint}?search=scope_&include_samples=true&limit=2').json()
        learners = response['data']['learners'] if endpoint == 'roster' else response['data']
        page = response['data']['page'] if endpoint == 'roster' else response['page']
        assert len(learners) == 2 and page['total'] == 3 and page['has_more']
        assert live_client.get(f'/api/teacher/{endpoint}?limit=51').status_code == 422


def test_roster_counts_people_once_and_bounds_activity_queries(live_client, integration_engine):
    from sqlalchemy import event
    with Session(integration_engine) as db:
        teacher = db.get(m.User, uid('teacher_demo'))
        users = [m.User(username=f'growth_{i}', password_hash=teacher.password_hash, role='learner') for i in range(3)]
        db.add_all(users); db.flush()
        db.add_all([m.TeacherAssignment(teacher_id=teacher.id, learner_id=u.id) for u in users])
        exercise = db.scalar(select(m.Exercise))
        db.add_all([m.Attempt(learner_id=users[0].id, exercise_id=exercise.id) for _ in range(30)])
        db.commit()
    live_client.post('/api/auth/login', json={'username':'teacher_demo','password':'integration-password-123'})
    statements = []
    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(integration_engine, 'before_cursor_execute', capture)
    try:
        result = live_client.get('/api/teacher/roster?search=growth_&limit=2').json()['data']
    finally:
        event.remove(integration_engine, 'before_cursor_execute', capture)
    assert result['page']['total'] == 3
    assert [u['investigations'] for u in result['learners']] == [30, 0]
    assert len({u['id'] for u in result['learners']}) == 2
    activity = [sql for sql in statements if 'FROM attempts' in sql]
    assert len(activity) == 1 and 'learner_id IN' in activity[0]
    roster_queries = [sql for sql in statements if 'teacher_assignments' in sql]
    assert roster_queries and all('password_hash' not in sql for sql in roster_queries)


def test_failures_restarts_and_quizzes_do_not_create_students(live_client, integration_engine):
    from sqlalchemy import func
    from app.content.catalog import catalog
    from app.schemas.classroom import SubmissionInput
    from app.services.quiz_submissions import save_submission
    from app.errors import AppError
    from test_integration import signup, reach_verification, send

    learner = signup(live_client)
    def identity_counts():
        with Session(integration_engine) as db:
            return tuple(db.scalar(select(func.count()).select_from(model)) for model in
                         (m.User, m.LearnerProfile, m.TeacherAssignment))
    before = identity_counts()
    exercise = catalog()[0]
    journey, base = reach_verification(live_client, exercise)
    attempt_id = journey['id']
    for _ in range(3):
        resumed = send(live_client, '/api/investigations/start', {'exercise_id': exercise['id']})
        assert resumed['id'] == attempt_id
        journey = send(live_client, base+'/independent', dict(task_id=journey['task']['id'],
            answer='wrong', explanation='I need another example.', reasoning_tag='guess'))
        assert journey['stage'] == 'support'
        with Session(integration_engine) as db:
            support = db.get(m.SupportModule, journey['support']['id'])
            support_id, answer = support.id, support.correct_choice
        send(live_client, base+'/support', dict(support_id=support_id, answer=answer))
        journey = send(live_client, base+'/continue-support', dict(support_id=support_id))
        assert identity_counts() == before

    with Session(integration_engine, expire_on_commit=False) as db:
        user = db.get(m.User, learner['id'])
        teacher_id = uid('teacher_demo')
        subject = db.scalar(select(m.ClassSubject).where(m.ClassSubject.teacher_id == teacher_id))
        course = db.scalar(select(m.ClassCourse).where(m.ClassCourse.subject_id == subject.id))
        quiz = m.ClassQuiz(teacher_id=teacher_id, subject_id=subject.id, title='Stable roster quiz', status='published')
        db.add(quiz); db.flush()
        question = m.QuizQuestion(quiz_id=quiz.id, course_id=course.id, prompt='Explain assignment.', expected_answer='Copy the value.', position=0)
        db.add(question); db.commit()
        payload = SubmissionInput(responses=[dict(question_id=question.id, answer='My answer', reasoning='My reasoning about assignment.')])
        first = save_submission(db, user, quiz.id, payload)
        with pytest.raises(AppError) as duplicate:
            save_submission(db, user, quiz.id, payload)
        assert duplicate.value.code == 'ALREADY_SUBMITTED'
        db.rollback()
        assert db.scalar(select(func.count()).select_from(m.QuizSubmission).where(
            m.QuizSubmission.quiz_id == quiz.id, m.QuizSubmission.learner_id == user.id)) == 1
        assert db.get(m.QuizSubmission, first.id).learner_id == user.id
    assert identity_counts() == before
    live_client.post('/api/auth/login', json={'username':'teacher_demo','password':'integration-password-123'})
    result = live_client.get('/api/teacher/roster?search='+learner['username']).json()['data']
    assert result['page']['total'] == 1
    assert result['learners'][0]['id'] == learner['id']
    assert result['learners'][0]['investigations'] == 1


def test_database_prevents_duplicate_profiles_and_enrollments(integration_engine):
    from sqlalchemy.exc import IntegrityError
    with Session(integration_engine) as db:
        for record in [m.LearnerProfile(user_id=uid('learner_a'), display_name='Duplicate'),
                       m.TeacherAssignment(teacher_id=uid('teacher_demo'), learner_id=uid('learner_a'))]:
            with pytest.raises(IntegrityError), db.begin_nested():
                db.add(record)
                db.flush()


def test_default_legacy_roster_is_bounded(integration_engine, live_client):
    with Session(integration_engine) as db:
        teacher = db.get(m.User, uid('teacher_demo'))
        users = [m.User(username=f'bounded_{i:03}', password_hash=teacher.password_hash, role='learner') for i in range(53)]
        db.add_all(users); db.flush()
        db.add_all([m.TeacherAssignment(teacher_id=teacher.id, learner_id=u.id) for u in users])
        db.commit()
    live_client.post('/api/auth/login', json={'username':'teacher_demo','password':'integration-password-123'})
    first = live_client.get('/api/teacher/learners?search=bounded_').json()
    assert len(first['data']) == 50 and first['page']['total'] == 53
    second = live_client.get('/api/teacher/learners?search=bounded_&offset=50').json()
    assert len(second['data']) == 3 and not second['page']['has_more']
    assert not ({u['id'] for u in first['data']} & {u['id'] for u in second['data']})
