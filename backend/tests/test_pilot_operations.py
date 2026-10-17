from datetime import timedelta
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app import models as m
from app.config import Settings


def test_database_schema_accepts_only_safe_postgres_identifiers(monkeypatch):
    monkeypatch.setenv('APP_DATABASE_SCHEMA', 'bm_pilot_october')
    assert Settings(_env_file=None).database_schema == 'bm_pilot_october'
    for invalid in ['public,evil', 'pilot; DROP SCHEMA public', '', 'pg_catalog', 'information_schema']:
        monkeypatch.setenv('APP_DATABASE_SCHEMA', invalid)
        with pytest.raises(ValueError): Settings(_env_file=None)


@pytest.mark.integration
def test_clean_pilot_has_curriculum_teacher_and_no_fake_learning(integration_engine):
    from app.seed import seed_curriculum, bootstrap_teacher
    from sqlalchemy import text
    from uuid import uuid4
    schema='bm_test_clean_'+uuid4().hex
    with integration_engine.connect() as connection:
        transaction=connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            m.Base.metadata.create_all(connection)
            with Session(connection) as db:
                seed_curriculum(db)
                teacher, invitation = bootstrap_teacher(db, 'pilot_teacher', 'pilot-password-123')
                assert teacher.is_synthetic is False
                assert teacher.data_origin == 'pilot'
                assert invitation.teacher_id == teacher.id
                assert db.scalar(select(func.count()).select_from(m.User)) == 1
                for model in [m.TeacherAssignment,m.Attempt,m.RetentionCheck,m.DelayedCheck,m.QuizSubmission]:
                    assert db.scalar(select(func.count()).select_from(model)) == 0
                assert db.scalar(select(func.count()).select_from(m.ClassSubject).where(m.ClassSubject.teacher_id == teacher.id)) == 1
        finally:
            # Transaction rollback removes only this test-created schema and its contents.
            if transaction.is_active: transaction.rollback()


@pytest.mark.integration
def test_session_cleanup_defaults_to_preview_and_keeps_live_sessions(integration_engine):
    from app.maintenance import cleanup_sessions
    with Session(integration_engine) as db:
        user = db.scalar(select(m.User))
        expired=m.AuthSession(user_id=user.id,expires_at=m.now()-timedelta(days=1))
        live=m.AuthSession(user_id=user.id,expires_at=m.now()+timedelta(days=1))
        db.add_all([expired,live]);db.flush()
        count=cleanup_sessions(db)
        assert count >= 1 and db.get(m.AuthSession,expired.id) is not None
        cleanup_sessions(db,apply=True)
        assert db.scalar(select(m.AuthSession).where(m.AuthSession.id==expired.id)) is None
        assert db.get(m.AuthSession,live.id) is not None
        db.rollback()


@pytest.mark.integration
def test_classroom_pagination_is_bounded_and_reports_continuation(live_client,integration_engine):
    from app.content.catalog import uid
    with Session(integration_engine) as db:
        teacher=db.get(m.User,uid('teacher_demo'))
        subject=db.scalar(select(m.ClassSubject).where(m.ClassSubject.teacher_id==teacher.id))
        db.add_all([m.ClassQuiz(teacher_id=teacher.id,subject_id=subject.id,title=f'Page {i}') for i in range(3)])
        db.commit()
    assert live_client.post('/api/auth/login',json={'username':'teacher_demo','password':'integration-password-123'}).status_code==200
    first=live_client.get('/api/classroom?quiz_limit=2').json()['data']
    assert len(first['quizzes'])==2 and first['quizzes_page']['has_more'] is True
    second=live_client.get('/api/classroom?quiz_limit=2&quiz_offset=2').json()['data']
    assert not ({q['id'] for q in first['quizzes']} & {q['id'] for q in second['quizzes']})
    assert live_client.get('/api/classroom?quiz_limit=101').status_code==422


@pytest.mark.integration
def test_classroom_batches_subjects_courses_and_exercises(integration_engine):
    from sqlalchemy import event
    from app.content.catalog import uid
    from app.services.classroom import overview
    with Session(integration_engine) as db:
        teacher=db.get(m.User,uid('teacher_demo'))
        for i in range(12):
            subject=m.ClassSubject(teacher_id=teacher.id,title=f'Batch subject {i}')
            db.add(subject);db.flush()
            db.add(m.ClassCourse(subject_id=subject.id,title='Topic',content='Authored text'))
        db.flush()
        queries=[]
        def record(*args): queries.append(args[2])
        event.listen(integration_engine,'before_cursor_execute',record)
        try: result=overview(db,teacher)
        finally: event.remove(integration_engine,'before_cursor_execute',record)
        assert len(result['subjects'])>=13
        assert len(queries)<=6
        db.rollback()


@pytest.mark.integration
def test_quiz_submission_pages_do_not_overlap_or_leak_peers(live_client,integration_engine):
    from app.content.catalog import uid
    with Session(integration_engine) as db:
        teacher=db.get(m.User,uid('teacher_demo'))
        subject=db.scalar(select(m.ClassSubject).where(m.ClassSubject.teacher_id==teacher.id))
        quiz=m.ClassQuiz(teacher_id=teacher.id,subject_id=subject.id,title='Submission pages',status='published')
        db.add(quiz);db.flush()
        for name in ['learner_a','learner_b','learner_c']:
            db.add(m.QuizSubmission(quiz_id=quiz.id,learner_id=uid(name),responses_json=[]))
        quiz_id=quiz.id;db.commit()
    live_client.post('/api/auth/login',json={'username':'teacher_demo','password':'integration-password-123'})
    first=live_client.get(f'/api/classroom/quizzes/{quiz_id}?submission_limit=2').json()['data']
    second=live_client.get(f'/api/classroom/quizzes/{quiz_id}?submission_limit=2&submission_offset=2').json()['data']
    assert len(first['submissions'])==2 and len(second['submissions'])==1
    assert first['submissions_page']['total']==3 and second['submissions_page']['has_more'] is False
    assert not ({s['id'] for s in first['submissions']} & {s['id'] for s in second['submissions']})
    live_client.post('/api/auth/login',json={'username':'learner_a','password':'integration-password-123'})
    own=live_client.get(f'/api/classroom/quizzes/{quiz_id}?submission_limit=100').json()['data']
    assert own['submissions_page']['total']==1 and own['submissions'][0]['learner']=='learner_a'


def test_bootstrap_secret_file_refuses_overwrite_and_nonignored_paths(tmp_path):
    from app.bootstrap import write_private_env
    with pytest.raises(ValueError): write_private_env(tmp_path/'credentials.txt',{'PASSWORD':'secret'})
    path=tmp_path/'.env.pilot'
    write_private_env(path,{'PASSWORD':'local-test-secret'})
    assert 'local-test-secret' in path.read_text()
    with pytest.raises(FileExistsError): write_private_env(path,{'PASSWORD':'replacement'})


@pytest.mark.integration
def test_teacher_timeline_pages_cover_all_event_types_without_overlap(live_client,integration_engine):
    from app.content.catalog import uid
    learner_id=uid('learner_a')
    with Session(integration_engine) as db:
        attempt=db.scalar(select(m.Attempt).where(m.Attempt.learner_id==learner_id))
        hypothesis=db.scalar(select(m.Hypothesis).where(m.Hypothesis.exercise_id==attempt.exercise_id))
        followup=db.scalar(select(m.FollowUp).where(m.FollowUp.exercise_id==attempt.exercise_id))
        support=db.scalar(select(m.SupportModule).where(m.SupportModule.exercise_id==attempt.exercise_id))
        exercise=db.get(m.Exercise,attempt.exercise_id)
        transfer=db.scalar(select(m.TransferTask).where(m.TransferTask.concept_id==exercise.concept_id))
        independent=db.scalar(select(m.IndependentTask).where(m.IndependentTask.concept_id==exercise.concept_id))
        common=dict(learner_id=learner_id,attempt_id=attempt.id,answer='test evidence',explanation='test reasoning',correct=False,evidence_json={})
        db.add_all([
            m.LearnerChallenge(attempt_id=attempt.id,system_hypothesis_id=hypothesis.id,alternative_hypothesis_id=hypothesis.id,learner_reason='test concern'),
            m.FollowUpSelection(attempt_id=attempt.id,follow_up_id=followup.id,divergence_score=1,burden_penalty=0,final_score=1,rationale='test selection'),
            m.SupportAttempt(attempt_id=attempt.id,support_module_id=support.id,selected_choice='test',correct=False),
            m.TransferAttempt(transfer_task_id=transfer.id,**common),
            m.IndependentAttempt(task_id=independent.id,**common),
            m.AdaptationEvent(learner_id=learner_id,attempt_id=attempt.id,old_assessment_json={},new_assessment_json={},reason='test adaptation'),
        ])
        db.commit()
    live_client.post('/api/auth/login',json={'username':'teacher_demo','password':'integration-password-123'})
    path=f'/api/teacher/learners/{learner_id}/timeline'
    first=live_client.get(path+'?event_limit=3').json()['data']
    assert len(first['events'])==3
    assert first['events_page']['total']>3
    seen=[];offset=0
    while True:
        page=live_client.get(path+f'?event_limit=3&event_offset={offset}').json()['data']
        seen.extend(event['id'] for event in page['events'])
        if not page['events_page']['has_more']: break
        offset=page['events_page']['next_offset']
    all_events=live_client.get(path+'?event_limit=100').json()['data']['events']
    assert seen==[event['id'] for event in all_events]
    assert len(set(seen))==len(seen)
    assert {'Interpretation','Reasoning evidence','Learner disagreement','Follow-up selection','Support interaction',
            'Transfer check','Independent check','Adaptation'} <= {event['kind'] for event in all_events}
    assert live_client.get(path+'?event_limit=101').status_code==422
