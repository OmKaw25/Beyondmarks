from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, literal, union_all
from sqlalchemy.orm import Session
from app import models as m
from app.db import get_db
from app.errors import fail
from app.security.dependencies import require_teacher
from app.services.journey_service import rows, record
from app.services.classroom import page_info

router = APIRouter(prefix='/api/teacher', tags=['teacher'])


@router.get('/invitation')
def invitation(teacher: m.User = Depends(require_teacher), db: Session = Depends(get_db)):
    code = db.scalar(select(m.TeacherInviteCode).where(m.TeacherInviteCode.teacher_id == teacher.id))
    if not code:
        fail(503, 'INVITATION_NOT_CONFIGURED', 'Your teacher code is not configured. Ask the administrator to apply the latest migration.')
    return {'data': {'code': code.code, 'teacher_code': code.code, 'student_code': code.student_code, 'teacher_id': teacher.id}}


@router.get('/learners')
def learners(teacher: m.User = Depends(require_teacher), db: Session = Depends(get_db)):
    counts=select(m.Attempt.learner_id,func.count().label('total')).join(m.TeacherAssignment,m.TeacherAssignment.learner_id==m.Attempt.learner_id).where(
        m.TeacherAssignment.teacher_id==teacher.id).group_by(m.Attempt.learner_id).subquery()
    assigned=db.execute(select(m.User,func.coalesce(counts.c.total,0)).join(m.TeacherAssignment,m.TeacherAssignment.learner_id==m.User.id)
        .outerjoin(counts,counts.c.learner_id==m.User.id).where(m.TeacherAssignment.teacher_id==teacher.id).order_by(m.User.username))
    return {'data':[dict(id=user.id,username=user.username,is_synthetic=user.is_synthetic,data_origin=user.data_origin,
                         investigations=total) for user,total in assigned]}


EVENT_GROUPS=[(m.LearnerEvidence,'Reasoning evidence'),(m.HypothesisAssessment,'Interpretation'),
    (m.LearnerChallenge,'Learner disagreement'),(m.FollowUpSelection,'Follow-up selection'),
    (m.SupportAttempt,'Support interaction'),(m.TransferAttempt,'Transfer check'),
    (m.IndependentAttempt,'Independent check'),(m.AdaptationEvent,'Adaptation')]


@router.get('/learners/{learner_id}')
@router.get('/learners/{learner_id}/timeline')
def timeline(learner_id: UUID, event_limit:int=Query(50,ge=1,le=100),event_offset:int=Query(0,ge=0),
             teacher: m.User = Depends(require_teacher), db: Session = Depends(get_db)):
    assignment=db.scalar(select(m.TeacherAssignment).where(m.TeacherAssignment.teacher_id==teacher.id,
                                                          m.TeacherAssignment.learner_id==str(learner_id)))
    if not assignment: fail(404,'NOT_FOUND','This learner is not assigned to you.')
    user=db.get(m.User,str(learner_id))
    # Union only identifiers/timestamps, so page size bounds expensive JSON evidence reads.
    index=union_all(*[select(model.id,model.created_at,model.attempt_id,literal(label).label('kind'))
        .join(m.Attempt,m.Attempt.id==model.attempt_id).where(m.Attempt.learner_id==user.id)
        for model,label in EVENT_GROUPS]).subquery()
    total=db.scalar(select(func.count()).select_from(index))
    page=list(db.execute(select(index).order_by(index.c.created_at.desc(),index.c.id.desc()).limit(event_limit).offset(event_offset)).mappings())
    attempts={a.id:a for a in db.scalars(select(m.Attempt).where(m.Attempt.id.in_({event['attempt_id'] for event in page})))} if page else {}
    exercises={e.id:e.title for e in db.scalars(select(m.Exercise).where(m.Exercise.id.in_({a.exercise_id for a in attempts.values()})))} if attempts else {}
    event_rows={}
    for model,label in EVENT_GROUPS:
        ids=[event['id'] for event in page if event['kind']==label]
        if ids:
            for event in db.scalars(select(model).where(model.id.in_(ids))): event_rows[(label,event.id)]=event
    hypothesis_ids=set()
    for (label,_),event in event_rows.items():
        if label=='Learner disagreement':
            hypothesis_ids.update([event.system_hypothesis_id,event.alternative_hypothesis_id])
    hypotheses={h.id:h.label for h in db.scalars(select(m.Hypothesis).where(m.Hypothesis.id.in_(hypothesis_ids)))} if hypothesis_ids else {}
    events=[]
    for item in page:
        event=event_rows[(item['kind'],item['id'])]
        attempt=attempts[event.attempt_id]
        details=record(event)
        label='Reflection challenge' if isinstance(event,m.IndependentAttempt) and event.evidence_json.get('phase')=='reflection' else item['kind']
        if isinstance(event,m.LearnerChallenge):
            details['system_hypothesis_label']=hypotheses.get(event.system_hypothesis_id)
            details['alternative_hypothesis_label']=hypotheses.get(event.alternative_hypothesis_id)
        events.append(dict(id=event.id,kind=label,created_at=event.created_at,is_synthetic=attempt.is_synthetic or user.is_synthetic,
                           investigation=exercises[attempt.exercise_id],details=details))
    return {'data':dict(id=user.id,username=user.username,is_synthetic=user.is_synthetic,data_origin=user.data_origin,
                        events=events,events_page=page_info(total,event_limit,event_offset),
                        retention=[record(c) for c in rows(db,m.RetentionCheck,m.RetentionCheck.learner_id==user.id)])}
