from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models as m
from app.db import get_db
from app.errors import fail
from app.schemas import StartAttempt, Correction, Challenge, Answer, TaskResponse, SupportIdentity, SupportAnswer, AgencyAction
from app.security.dependencies import require_learner
from app.services import journey_service as journey

router = APIRouter(prefix='/api', tags=['learning'])


@router.get('/learner/home')
def home(user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    exercise_rows = db.execute(select(m.Exercise, m.Concept.name).join(m.Concept, m.Concept.id == m.Exercise.concept_id)
                               .where(m.Exercise.active == True).order_by(m.Exercise.created_at, m.Exercise.id)).all()
    from app.services.classroom import course_scores, teacher_ids
    from app.services.quiz_grading import recommendation_key
    scores=course_scores(db,user.id)
    concept_scores={}
    courses=db.scalars(select(m.ClassCourse).join(m.ClassSubject,m.ClassSubject.id==m.ClassCourse.subject_id)
                       .where(m.ClassSubject.teacher_id.in_(teacher_ids(db,user))))
    for course in courses:
        if course.concept_id and course.id in scores:
            concept_scores[course.concept_id]=min(scores[course.id],concept_scores.get(course.concept_id,100))
    exercise_views=[dict(id=e.id,title=e.title,concept=concept_name,
                         score=concept_scores.get(e.concept_id),position=i) for i,(e,concept_name) in enumerate(exercise_rows)]
    exercise_views.sort(key=recommendation_key)
    # PostgreSQL DISTINCT ON bounds the returned history before loading rows.
    # Filter sample activity before choosing the latest real attempt.
    latest = (select(m.Attempt.id).where(m.Attempt.learner_id == user.id, m.Attempt.is_synthetic == False)
              .distinct(m.Attempt.exercise_id)
              .order_by(m.Attempt.exercise_id, m.Attempt.created_at.desc(), m.Attempt.id.desc()).subquery())
    attempts = db.execute(select(m.Attempt, m.Exercise.title, m.Concept.name)
                          .join(latest, latest.c.id == m.Attempt.id)
                          .join(m.Exercise, m.Exercise.id == m.Attempt.exercise_id)
                          .join(m.Concept, m.Concept.id == m.Exercise.concept_id)
                          .order_by(m.Attempt.created_at.desc(), m.Attempt.id.desc())).all()
    return {'data': dict(username=user.username, is_synthetic=user.is_synthetic,
                         exercises=exercise_views,
                         attempts=[dict(id=a.id, exercise_id=a.exercise_id,
                                        concept=concept_name,
                                        title=title, stage=a.stage, status=a.status,
                                        is_synthetic=a.is_synthetic, created_at=a.created_at,
                                        next_url=f'/{a.stage}/{a.id}' if a.stage not in ('review','retention') else f'/retention/{a.id}') for a,title,concept_name in attempts])}


@router.post('/investigations/start', status_code=201)
def start(payload: StartAttempt, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    result = journey.start(db, user, str(payload.exercise_id))
    db.commit()
    return {'data': result}


@router.get('/investigations/{attempt_id}')
@router.get('/investigations/{attempt_id}/diagnosis')
@router.get('/investigations/{attempt_id}/follow-up')
@router.get('/investigations/{attempt_id}/support')
@router.get('/investigations/{attempt_id}/transfer')
@router.get('/investigations/{attempt_id}/independent')
@router.get('/investigations/{attempt_id}/reflection')
def view(attempt_id: UUID, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return {'data': journey.snapshot(db, journey.owned(db, user.id, str(attempt_id)))}


def mutate(db, user, attempt_id, operation, payload=None):
    attempt = journey.owned(db, user.id, str(attempt_id), lock=True)
    if operation is not journey.agency and attempt.state.get('agency', {}).get('paused'):
        fail(409, 'INVESTIGATION_PAUSED', 'Resume this investigation before submitting your next response.')
    operation(db, attempt, payload) if payload is not None else operation(db, attempt)
    db.flush()
    result = journey.snapshot(db, attempt)
    db.commit()
    return {'data': result}


@router.post('/investigations/{attempt_id}/agency')
def agency(attempt_id: UUID, payload: AgencyAction, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, journey.agency, payload)


@router.post('/investigations/{attempt_id}/correction')
def correction(attempt_id: UUID, payload: Correction, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, journey.correct, payload)


@router.post('/investigations/{attempt_id}/challenge')
def challenge(attempt_id: UUID, payload: Challenge, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, journey.challenge, payload)


@router.post('/investigations/{attempt_id}/select-follow-up')
def select_followup(attempt_id: UUID, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, journey.select_next)


@router.post('/investigations/{attempt_id}/follow-up')
def answer_followup(attempt_id: UUID, payload: Answer, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, journey.answer_followup, payload)


@router.post('/investigations/{attempt_id}/support')
def answer_support(attempt_id: UUID, payload: SupportAnswer, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, journey.answer_support, payload)


@router.post('/investigations/{attempt_id}/transfer')
def transfer(attempt_id: UUID, payload: TaskResponse, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, lambda d,a,p: journey.answer_task(d,a,p,False), payload)


@router.post('/investigations/{attempt_id}/continue-support')
def continue_support(attempt_id: UUID, payload: SupportIdentity, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, journey.continue_support, payload)


@router.post('/investigations/{attempt_id}/independent')
def independent(attempt_id: UUID, payload: TaskResponse, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, lambda d,a,p: journey.answer_task(d,a,p,True), payload)


@router.post('/investigations/{attempt_id}/reflection')
def reflection(attempt_id: UUID, payload: TaskResponse, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return mutate(db, user, attempt_id, lambda d,a,p: journey.answer_task(d,a,p,True,reflection=True), payload)


@router.get('/retention')
def retention(user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    checks = journey.rows(db, m.RetentionCheck, m.RetentionCheck.learner_id == user.id)
    return {'data': [dict(id=c.id, concept=db.get(m.Concept,c.concept_id).name, outcome=c.outcome,
                         check_date=c.check_date, is_synthetic=c.is_synthetic, explanation=c.explanation,
                         adaptation_required=c.adaptation_required, adaptation_attempt_id=c.adaptation_attempt_id) for c in checks]}


@router.post('/retention/{check_id}/adapt')
def adapt_retention(check_id: UUID, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    from app.services.adaptation_engine import adapt
    check = db.scalar(select(m.RetentionCheck).where(m.RetentionCheck.id == str(check_id), m.RetentionCheck.learner_id == user.id).with_for_update())
    if not check:
        fail(404, 'NOT_FOUND', 'This retention check was not found.')
    if check.outcome != 'FAIL':
        fail(409, 'NO_ADAPTATION_NEEDED', 'This check does not require adaptation.')
    if check.adaptation_attempt_id:
        return {'data': journey.snapshot(db, journey.owned(db, user.id, check.adaptation_attempt_id))}
    baseline = journey.owned(db, user.id, check.baseline_attempt_id)
    attempt = m.Attempt(learner_id=user.id, exercise_id=baseline.exercise_id, stage='support',
                        is_synthetic=check.is_synthetic, state=dict(baseline.state))
    db.add(attempt); db.flush()
    for evidence in journey.rows(db, m.LearnerEvidence, m.LearnerEvidence.attempt_id == baseline.id):
        journey.append_evidence(db, attempt, evidence.evidence_key, dict(evidence.value_json), 'synthetic-baseline')
    journey.append_evidence(db, attempt, 'independent_failed', {'check_id':check.id, 'is_synthetic':check.is_synthetic}, 'retention')
    adapt(db, attempt, 'The synthetic delayed check did not confirm retained understanding. This is a demonstration, not a longitudinal observation.', source_check_id=check.id)
    check.adaptation_attempt_id = attempt.id
    db.flush()
    result = journey.snapshot(db, attempt)
    db.commit()
    return {'data': result}
