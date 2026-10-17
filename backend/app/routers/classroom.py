from uuid import UUID
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app import models as m
from app.db import get_db
from app.security.dependencies import get_current_user,require_teacher,require_learner
from app.schemas.classroom import SubjectInput,CourseInput,QuizInput,SubmissionInput
from app.services import classroom as service
from app.services.quiz_submissions import save_submission,evaluate_submission

router=APIRouter(prefix='/api/classroom',tags=['classroom'])


@router.get('')
def overview(quiz_limit:int=Query(20,ge=1,le=100),quiz_offset:int=Query(0,ge=0),user:m.User=Depends(get_current_user),db:Session=Depends(get_db)):
    return {'data':service.overview(db,user,quiz_limit,quiz_offset)}


@router.post('/subjects',status_code=201)
def create_subject(payload:SubjectInput,user:m.User=Depends(require_teacher),db:Session=Depends(get_db)):
    subject=service.create_subject(db,user,payload);db.commit()
    return {'data':{'id':subject.id}}


@router.post('/subjects/{subject_id}/courses',status_code=201)
def add_course(subject_id:UUID,payload:CourseInput,user:m.User=Depends(require_teacher),db:Session=Depends(get_db)):
    course=service.add_course(db,user,str(subject_id),payload);db.commit()
    return {'data':{'id':course.id}}


@router.post('/quizzes',status_code=201)
def create_quiz(payload:QuizInput,user:m.User=Depends(require_teacher),db:Session=Depends(get_db)):
    quiz=service.create_quiz(db,user,payload);db.commit()
    return {'data':service.quiz_view(db,user,quiz)}


@router.get('/quizzes/{quiz_id}')
def quiz_view(quiz_id:UUID,submission_limit:int=Query(20,ge=1,le=100),submission_offset:int=Query(0,ge=0),user:m.User=Depends(get_current_user),db:Session=Depends(get_db)):
    return {'data':service.quiz_view(db,user,service.quiz_for(db,user,str(quiz_id)),submission_limit,submission_offset)}


@router.post('/quizzes/{quiz_id}/publish')
def publish(quiz_id:UUID,user:m.User=Depends(require_teacher),db:Session=Depends(get_db)):
    quiz=service.quiz_for(db,user,str(quiz_id),lock=True)
    if quiz.status=='draft': quiz.status='published';quiz.published_at=m.now()
    db.commit()
    return {'data':service.quiz_view(db,user,quiz)}


@router.post('/quizzes/{quiz_id}/update')
def update(quiz_id:UUID,payload:QuizInput,user:m.User=Depends(require_teacher),db:Session=Depends(get_db)):
    quiz=service.edit_quiz(db,user,str(quiz_id),payload);db.commit()
    return {'data':service.quiz_view(db,user,quiz)}


@router.post('/quizzes/{quiz_id}/submit',status_code=201)
def submit(quiz_id:UUID,payload:SubmissionInput,user:m.User=Depends(require_learner),db:Session=Depends(get_db)):
    submission=save_submission(db,user,str(quiz_id),payload)
    evaluate_submission(db,user,submission.id)
    return {'data':service.quiz_view(db,user,service.quiz_for(db,user,str(quiz_id)))}


@router.post('/submissions/{submission_id}/retry')
def retry(submission_id:UUID,user:m.User=Depends(get_current_user),db:Session=Depends(get_db)):
    submission=evaluate_submission(db,user,str(submission_id))
    return {'data':service.quiz_view(db,user,service.quiz_for(db,user,submission.quiz_id))}
