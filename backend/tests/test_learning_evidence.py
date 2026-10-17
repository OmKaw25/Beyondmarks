"""Real-time scheduling, answer privacy, grading, and append-only review integration."""
from copy import deepcopy
from datetime import timedelta
from uuid import uuid4
import pytest
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app import models as m
from app.errors import AppError
from app.schemas.learning_evidence import DelayedAnswer, ReviewInput, DisputeInput
from app.services import delayed_retention as retention, feedback_review as reviews


@pytest.fixture
def evidence_db(integration_engine):
    with Session(integration_engine, expire_on_commit=False) as db:
        try:
            yield db
        finally:
            db.rollback()


def user(db, role='learner', synthetic=False):
    row = m.User(username='evidence_' + uuid4().hex[:16], password_hash='unused-test-password', role=role,
                 is_synthetic=synthetic)
    db.add(row)
    db.flush()
    return row


def completed(db, learner, days_ago=0, synthetic=False):
    exercise = db.scalar(select(m.Exercise).join(m.Concept).where(m.Concept.slug == 'variables', m.Exercise.active == True))
    row = m.Attempt(learner_id=learner.id, exercise_id=exercise.id, stage='retention', status='complete',
                    is_synthetic=synthetic, completed_at=m.now() - timedelta(days=days_ago), state={})
    db.add(row)
    db.flush()
    return row


def answer(check, correct=True, reason=True):
    task = check.task_json
    reasoning_tag = task['correct_tag'] if reason else next(o['value'] for o in task['reasoning_options'] if o['value'] != task['correct_tag'])
    return DelayedAnswer(answer=task['expected_output'] if correct else 'incorrect answer',
                         explanation='I tracked each assignment separately.', reasoning_tag=reasoning_tag)


@pytest.mark.integration
def test_delayed_schedule_is_real_idempotent_private_and_unseen(evidence_db):
    db = evidence_db
    learner = user(db)
    attempt = completed(db, learner)
    checks = retention.schedule_for_attempt(db, attempt)
    assert [c.interval_days for c in checks] == [7, 30]
    assert len(retention.schedule_for_attempt(db, attempt)) == 2
    assert len({c.task_id for c in checks}) == 2
    for check in checks:
        assert check.due_at == attempt.completed_at + timedelta(days=check.interval_days)
        view = retention.check_view(db, check, detail=True)
        assert view['status'] == 'scheduled' and view['task'] is None
        assert view['result'] is None and view['response'] is None
        with pytest.raises(AppError) as error:
            retention.submit_check(db, learner, check.id, answer(check))
        assert error.value.code == 'CHECK_NOT_DUE'
    # Ordinary practice cannot consume a question reserved for a delayed check.
    from app.services.practice_variants import fresh_task
    assert fresh_task(db, attempt, 'independent').id not in {c.task_id for c in checks}
    stranger = user(db)
    with pytest.raises(AppError) as error:
        retention.check_for(db, stranger, checks[0].id)
    assert error.value.status == 404
    assert retention.list_checks(db, stranger) == {'checks': []}
    assert retention.schedule_for_attempt(db, completed(db, learner, synthetic=True)) == []
    synthetic_user = user(db, synthetic=True)
    assert retention.schedule_for_attempt(db, completed(db, synthetic_user)) == []
    unfinished = completed(db, learner)
    unfinished.status = 'active'
    assert retention.schedule_for_attempt(db, unfinished) == []


@pytest.mark.integration
def test_delayed_due_grading_needs_answer_and_reasoning_and_is_immutable(evidence_db):
    db = evidence_db
    learner = user(db)
    baseline = completed(db, learner, days_ago=8)
    check = retention.schedule_for_attempt(db, baseline)[0]
    public = retention.check_view(db, check, detail=True)
    assert public['status'] == 'due'
    assert not {'expected_output', 'correct_tag', 'correct_answer', 'interaction_json'} & set(public['task'])
    assert 'correct_answer' not in public['task']['interaction']
    result = retention.submit_check(db, learner, check.id, answer(check))
    assert result['status'] == 'passed' and result['completed_at'] >= check.due_at
    assert result['result']['reasoning_supported'] and result['result']['explanation_present']
    assert result['adaptation_attempt_id'] is None
    saved = deepcopy(check.answer_json)
    with pytest.raises(AppError) as error:
        retention.submit_check(db, learner, check.id, answer(check, correct=False))
    assert error.value.code == 'CHECK_RECORDED'
    assert check.answer_json == saved
    assert baseline.status == 'complete'


@pytest.mark.integration
def test_missed_check_stays_due_and_failed_checks_reuse_adaptation(evidence_db):
    db = evidence_db
    learner = user(db)
    baseline = completed(db, learner, days_ago=45)
    checks = retention.schedule_for_attempt(db, baseline)
    assert all(retention.check_view(db, c)['status'] == 'due' and c.result_json is None for c in checks)
    first = retention.submit_check(db, learner, checks[0].id, answer(checks[0], reason=False))
    assert first['result']['correct'] is True and first['status'] == 'failed'
    assert first['adaptation_attempt_id'] and first['next_url'].startswith('/support/')
    second = retention.submit_check(db, learner, checks[1].id, answer(checks[1], correct=False))
    assert second['adaptation_attempt_id'] == first['adaptation_attempt_id']
    assert baseline.status == 'complete' and baseline.stage == 'retention'
    adaptation = db.get(m.Attempt, first['adaptation_attempt_id'])
    assert adaptation.is_synthetic is False and adaptation.status == 'active'
    assert db.scalar(select(func.count()).select_from(m.LearnerEvidence).where(m.LearnerEvidence.attempt_id == adaptation.id)) == 2
    assert db.scalar(select(func.count()).select_from(m.AdaptationEvent).where(m.AdaptationEvent.attempt_id == adaptation.id)) == 1


@pytest.mark.integration
def test_mark_demo_preserves_checks_but_separates_provenance_and_completed_evidence(evidence_db):
    db = evidence_db
    learner = user(db)
    learner.data_origin = 'pilot'
    baseline = completed(db, learner, days_ago=45)
    checks = retention.schedule_for_attempt(db, baseline)
    retention.submit_check(db, learner, checks[0].id, answer(checks[0]))
    saved = deepcopy(checks[0].answer_json)
    assert retention.list_checks(db, learner)['checks'][0]['data_origin'] == 'pilot'
    from app.maintenance import mark_demo_accounts
    assert mark_demo_accounts(db, [learner.username]) == 1
    db.flush()
    assert retention.list_checks(db, learner) == {'checks': []}
    teacher_view = retention.list_checks(db, learner, include_demo=True, include_completed=True)['checks']
    assert len(teacher_view) == 2
    assert all(c['is_synthetic'] and c['data_origin'] == 'demo' for c in teacher_view)
    assert all('task' not in c and 'expected_output' not in c for c in teacher_view)
    assert teacher_view[0]['response'] == saved and teacher_view[0]['result']['passed'] is True
    assert teacher_view[1]['status'] == 'due' and teacher_view[1]['response'] is None and teacher_view[1]['result'] is None
    assert retention.check_view(db, checks[0], detail=True)['is_synthetic'] is True
    assert checks[0].answer_json == saved and db.get(m.DelayedCheck, checks[1].id) is not None
    # Continuing an archived demonstration cannot create a new "real" adaptation.
    failed = retention.submit_check(db, learner, checks[1].id, answer(checks[1], correct=False))
    assert db.get(m.Attempt, failed['adaptation_attempt_id']).is_synthetic is True


def graded_submission(db):
    teacher, learner = user(db, 'teacher'), user(db)
    db.add(m.TeacherAssignment(teacher_id=teacher.id, learner_id=learner.id))
    subject = m.ClassSubject(teacher_id=teacher.id, title='Audited science', description='')
    db.add(subject); db.flush()
    course = m.ClassCourse(subject_id=subject.id, title='Evidence', content='Explain the evidence.', position=0)
    quiz = m.ClassQuiz(teacher_id=teacher.id, subject_id=subject.id, title='Evidence quiz', status='published')
    db.add_all([course, quiz]); db.flush()
    question = m.QuizQuestion(quiz_id=quiz.id, course_id=course.id, prompt='Why?', expected_answer='Because', rubric='', position=0)
    db.add(question); db.flush()
    evaluation = {'source': 'Saved test feedback', 'questions': [dict(question_id=question.id, answer_score=30,
                  reasoning_score=40, feedback='Explain more.', misconception='Missing evidence', needs_review=True)]}
    submission = m.QuizSubmission(quiz_id=quiz.id, learner_id=learner.id, responses_json=[dict(question_id=question.id,
                                   answer='Because', reasoning='Here is evidence.')], evaluation_json=evaluation, status='graded')
    db.add(submission); db.flush()
    return teacher, learner, question, submission


@pytest.mark.integration
def test_teacher_review_resolves_dispute_preserves_original_and_updates_score(evidence_db):
    db = evidence_db
    teacher, learner, question, submission = graded_submission(db)
    original = deepcopy(submission.evaluation_json)
    response = deepcopy(submission.responses_json)
    dispute = reviews.add_dispute(db, learner, submission.id, DisputeInput(question_id=question.id, reason='My reasoning cites the evidence.'))['disputes'][0]
    assert dispute['status'] == 'open'
    with pytest.raises(AppError) as error:
        reviews.add_dispute(db, learner, submission.id, DisputeInput(question_id=question.id, reason='Duplicate concern'))
    assert error.value.code == 'DISPUTE_OPEN'
    payload = ReviewInput(question_id=question.id, answer_score=90, reasoning_score=80,
                          feedback='Your evidence supports the conclusion.', reason='The AI missed the cited evidence.', dispute_id=dispute['id'])
    reviewed = reviews.add_review(db, teacher, submission.id, payload)
    assert reviewed['disputes'][0]['status'] == 'resolved'
    assert reviewed['evaluation']['questions'][0]['answer_score'] == 90
    assert reviewed['evaluation']['questions'][0]['needs_review'] is False
    assert submission.evaluation_json == original and submission.responses_json == response
    from app.services.classroom import course_scores
    assert course_scores(db, learner.id)[question.course_id] == 85
    assert reviews.effective_evaluation(db, submission)['questions'][0]['reviewed'] is True
    assert reviews.effective_evaluation(db, submission, []) == original
    with pytest.raises(AppError) as error:
        reviews.add_review(db, teacher, submission.id, payload)
    assert error.value.code == 'DISPUTE_RESOLVED'
    # A later correction is a new audit event; zero scores are not treated as missing.
    second = payload.model_copy(update={'answer_score': 0, 'reasoning_score': 0, 'reason': 'Follow-up correction', 'dispute_id': None})
    latest = reviews.add_review(db, teacher, submission.id, second)
    assert len(latest['reviews']) == 2 and latest['reviews'][0]['answer_score'] == 90
    assert latest['evaluation']['questions'][0]['answer_score'] == 0
    assert course_scores(db, learner.id)[question.course_id] == 0


@pytest.mark.integration
def test_review_scope_and_question_membership(evidence_db):
    db = evidence_db
    teacher, learner, question, submission = graded_submission(db)
    for outsider in [user(db), user(db, 'teacher')]:
        with pytest.raises(AppError) as error:
            reviews.submission_for(db, outsider, submission.id)
        assert error.value.status == 404
    with pytest.raises(AppError) as error:
        reviews.add_dispute(db, learner, submission.id, DisputeInput(question_id=uuid4(), reason='Wrong question'))
    assert error.value.code == 'INVALID_QUESTION'
    with pytest.raises(AppError) as error:
        reviews.add_review(db, learner, submission.id, ReviewInput(question_id=question.id, answer_score=100,
            reasoning_score=100, feedback='My edit', reason='Not authorized'))
    assert error.value.status == 403
    submission.status = 'pending'
    with pytest.raises(AppError) as error:
        reviews.add_dispute(db, learner, submission.id, DisputeInput(question_id=question.id, reason='Pending'))
    assert error.value.code == 'FEEDBACK_PENDING'


def test_feedback_inputs_reject_blank_reason_and_hidden_key_injection():
    with pytest.raises(ValidationError):
        DisputeInput(question_id=uuid4(), reason='   ')
    with pytest.raises(ValidationError):
        DelayedAnswer(answer='1', explanation='Because', reasoning_tag='valid', expected_output='1')
    with pytest.raises(ValidationError):
        ReviewInput(question_id=uuid4(), answer_score=101, reasoning_score=80, feedback='Feedback', reason='Reason')


@pytest.mark.integration
def test_retention_and_review_http_contracts(live_client, integration_engine):
    client = live_client
    def post(path, payload):
        response = client.post('/api' + path, json=payload)
        assert response.status_code in (200, 201), response.text
        return response.json()['data']
    assert client.get('/api/retention/checks').status_code == 401
    post('/auth/login', dict(username='teacher_demo', password='integration-password-123'))
    invitation = client.get('/api/teacher/invitation').json()['data']
    assert client.get('/api/retention/checks').status_code == 403
    learner = post('/auth/signup', dict(username='delay_' + uuid4().hex[:12], password='integration-password-123',
                                       role='learner', invite_code=invitation['student_code']))
    with Session(integration_engine, expire_on_commit=False) as db:
        learner_row = db.get(m.User, learner['id'])
        check = retention.schedule_for_attempt(db, completed(db, learner_row, days_ago=8))[0]
        check_id, body = check.id, answer(check).model_dump()
        db.commit()
    listing = client.get('/api/retention/checks').json()['data']['checks']
    assert len(listing) == 2 and {row['status'] for row in listing} == {'due', 'scheduled'}
    detail = client.get('/api/retention/checks/' + check_id).json()['data']
    assert detail['task']['reasoning_options'] and 'correct_tag' not in detail['task']
    assert post('/retention/checks/' + check_id + '/submit', body)['status'] == 'passed'
    assert client.post('/api/retention/checks/' + check_id + '/submit', json=body).status_code == 409
    assert client.post('/api/retention/checks/' + check_id + '/submit', json={**body, 'result': {'passed': True}}).status_code == 422
    # Exercise review HTTP paths on owned persisted records without an external AI request.
    with Session(integration_engine, expire_on_commit=False) as db:
        teacher_row = db.scalar(select(m.User).where(m.User.username == 'teacher_demo'))
        _, _, question, submission = graded_submission(db)
        quiz = db.get(m.ClassQuiz, submission.quiz_id)
        quiz.teacher_id = teacher_row.id
        submission.learner_id = learner['id']
        submission_id, question_id = submission.id, question.id
        db.commit()
    path = '/classroom/submissions/' + submission_id
    data = post(path + '/disputes', dict(question_id=question_id, reason='My answer uses equivalent reasoning.'))
    dispute_id = data['disputes'][0]['id']
    assert client.post('/api' + path + '/reviews', json=dict(question_id=question_id, answer_score=90,
        reasoning_score=90, feedback='Student edit', reason='Not permitted')).status_code == 403
    post('/auth/login', dict(username='teacher_demo', password='integration-password-123'))
    teacher_checks = client.get('/api/teacher/learners/' + learner['id'] + '/retention')
    assert teacher_checks.status_code == 200
    assert len(teacher_checks.json()['data']['checks']) == 2
    assert all('task' not in row and 'expected_output' not in row for row in teacher_checks.json()['data']['checks'])
    completed_check, future_check = teacher_checks.json()['data']['checks']
    assert completed_check['response'] == body and completed_check['result']['passed'] is True
    assert completed_check['data_origin'] == learner.get('data_origin', 'unverified')
    assert future_check['response'] is None and future_check['result'] is None
    assert 'correct_answer' not in str(teacher_checks.json()) and 'correct_tag' not in str(teacher_checks.json())
    assert client.get('/api/teacher/learners/' + str(uuid4()) + '/retention').status_code == 404
    data = post(path + '/reviews', dict(question_id=question_id, answer_score=90, reasoning_score=90,
                feedback='Equivalent reasoning accepted.', reason='Reviewed the student evidence.', dispute_id=dispute_id))
    assert data['original_evaluation']['questions'][0]['answer_score'] == 30
    assert data['evaluation']['questions'][0]['answer_score'] == 90
    assert data['disputes'][0]['status'] == 'resolved'
    post('/auth/signup', dict(username='delay_peer_' + uuid4().hex[:10], password='integration-password-123',
                             role='learner', invite_code=invitation['student_code']))
    assert client.get('/api' + path + '/reviews').status_code == 404
    assert client.get('/api/retention/checks/' + check_id).status_code == 404
    assert client.get('/api/teacher/learners/' + learner['id'] + '/retention').status_code == 403
