"""Save immutable responses before claiming a bounded external grading request."""
from datetime import timedelta
from uuid import uuid4
from sqlalchemy import select
from app import models as m
from app.errors import fail
from app.services.classroom import quiz_for, questions_for, refresh_course_progress
from app.services.quiz_grading import grade_questions, GradingUnavailable


def save_submission(db,user,quiz_id,payload):
    quiz=quiz_for(db,user,quiz_id,lock=True)
    previous=db.scalar(select(m.QuizSubmission).where(m.QuizSubmission.quiz_id==quiz.id,m.QuizSubmission.learner_id==user.id))
    if previous: fail(409,'ALREADY_SUBMITTED','Your answers are already saved. Open your results to review them.')
    expected={q.id for q in questions_for(db,quiz.id)}
    supplied=[str(r.question_id) for r in payload.responses]
    if len(supplied)!=len(set(supplied)) or set(supplied)!=expected:
        fail(422,'INCOMPLETE_QUIZ','Answer every question exactly once.')
    submission=m.QuizSubmission(quiz_id=quiz.id,learner_id=user.id,responses_json=[r.model_dump(mode='json') for r in payload.responses])
    db.add(submission);db.flush();db.commit()
    return submission


def evaluate_submission(db,user,submission_id):
    submission=db.scalar(select(m.QuizSubmission).where(m.QuizSubmission.id==submission_id).with_for_update().execution_options(populate_existing=True))
    if not submission: fail(404,'NOT_FOUND','This submission was not found.')
    quiz=quiz_for(db,user,submission.quiz_id)
    if user.role=='learner' and submission.learner_id!=user.id:
        fail(404,'NOT_FOUND','This submission was not found.')
    if submission.status=='graded':
        db.commit();return submission
    if submission.status=='grading' and submission.grading_started_at and submission.grading_started_at>m.now()-timedelta(minutes=2):
        fail(409,'GRADING_IN_PROGRESS','Your feedback is being prepared. Refresh in a moment.')
    token=str(uuid4())
    submission.status='grading';submission.grading_token=token;submission.grading_started_at=m.now();submission.error_code=None
    answers={r['question_id']:r for r in submission.responses_json}
    questions=[dict(question_id=q.id,prompt=q.prompt,expected_answer=q.expected_answer,rubric=q.rubric,
                    answer=answers[q.id]['answer'],reasoning=answers[q.id]['reasoning']) for q in questions_for(db,quiz.id)]
    db.commit()  # Release locks while the external request runs.
    try:
        evaluation=grade_questions(questions);error=None
    except GradingUnavailable as exc:
        evaluation=None;error=exc.code
    db.expire_all()
    submission=db.scalar(select(m.QuizSubmission).where(m.QuizSubmission.id==submission_id).with_for_update())
    if submission.grading_token==token:
        submission.status='graded' if evaluation else 'pending'
        submission.evaluation_json=evaluation;submission.error_code=error
        submission.graded_at=m.now() if evaluation else None
        submission.grading_token=None
        if evaluation:
            db.flush()
            refresh_course_progress(db,submission.learner_id)
    db.commit()
    return submission
