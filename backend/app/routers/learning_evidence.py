from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models as m
from app.db import get_db
from app.errors import fail
from app.security.dependencies import get_current_user, require_learner, require_teacher
from app.schemas.learning_evidence import DelayedAnswer, ReviewInput, DisputeInput
from app.services import delayed_retention as retention, feedback_review as review

router = APIRouter(prefix='/api', tags=['learning-evidence'])


@router.get('/retention/checks')
def checks(user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return {'data': retention.list_checks(db, user)}


@router.get('/teacher/learners/{learner_id}/retention')
def teacher_checks(learner_id: UUID, user: m.User = Depends(require_teacher), db: Session = Depends(get_db)):
    learner = db.scalar(select(m.User).join(m.TeacherAssignment, m.TeacherAssignment.learner_id == m.User.id)
                        .where(m.User.id == str(learner_id), m.User.role == 'learner', m.User.active == True,
                               m.TeacherAssignment.teacher_id == user.id))
    if not learner:
        fail(404, 'NOT_FOUND', 'This student is not in your class.')
    return {'data': retention.list_checks(db, learner, include_demo=True, include_completed=True)}


@router.get('/retention/checks/{check_id}')
def check_detail(check_id: UUID, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    return {'data': retention.check_view(db, retention.check_for(db, user, str(check_id)), detail=True)}


@router.post('/retention/checks/{check_id}/submit')
def submit_check(check_id: UUID, payload: DelayedAnswer, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    data = retention.submit_check(db, user, str(check_id), payload)
    db.commit()
    return {'data': data}


@router.get('/classroom/submissions/{submission_id}/reviews')
def reviews(submission_id: UUID, user: m.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {'data': review.review_view(db, review.submission_for(db, user, str(submission_id)))}


@router.post('/classroom/submissions/{submission_id}/reviews', status_code=201)
def add_review(submission_id: UUID, payload: ReviewInput, user: m.User = Depends(require_teacher), db: Session = Depends(get_db)):
    data = review.add_review(db, user, str(submission_id), payload)
    db.commit()
    return {'data': data}


@router.post('/classroom/submissions/{submission_id}/disputes', status_code=201)
def add_dispute(submission_id: UUID, payload: DisputeInput, user: m.User = Depends(require_learner), db: Session = Depends(get_db)):
    data = review.add_dispute(db, user, str(submission_id), payload)
    db.commit()
    return {'data': data}
