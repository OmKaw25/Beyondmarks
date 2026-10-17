"""Append-only teacher corrections and learner disputes preserve original AI output."""
from copy import deepcopy
from sqlalchemy import select
from app import models as m
from app.errors import fail


def effective_evaluation(db, submission, reviews=None):
    if reviews is None:
        reviews = list(db.scalars(select(m.TeacherReview).where(m.TeacherReview.submission_id == submission.id)))
    latest = {}
    for review in sorted(reviews, key=lambda r: (r.created_at, r.id)):
        if review.submission_id == submission.id:
            latest[review.question_id] = review
    if submission.evaluation_json is None and not latest:
        return None
    result = deepcopy(submission.evaluation_json) if submission.evaluation_json is not None else {'source': 'teacher', 'questions': []}
    existing = {q['question_id'] for q in result.get('questions', [])}
    # Only assessed responses appear: missing feedback is never a zero score.
    for response in submission.responses_json:
        question_id = response['question_id']
        if question_id in latest and question_id not in existing:
            result['questions'].append({'question_id': question_id})
    for question in result.get('questions', []):
        review = latest.get(question['question_id'])
        if review:
            question.update(answer_score=review.answer_score, reasoning_score=review.reasoning_score,
                            feedback=review.feedback, misconception=review.misconception, needs_review=False,
                            reviewed=True, review_id=review.id, review_reason=review.reason)
    return result


def submission_for(db, user, submission_id, lock=False):
    query = select(m.QuizSubmission).where(m.QuizSubmission.id == submission_id)
    submission = db.scalar(query.with_for_update().execution_options(populate_existing=True) if lock else query)
    quiz = db.get(m.ClassQuiz, submission.quiz_id) if submission else None
    allowed = bool(submission and quiz)
    if allowed and user.role == 'teacher':
        allowed = quiz.teacher_id == user.id and bool(db.scalar(select(m.TeacherAssignment.id).where(
            m.TeacherAssignment.teacher_id == user.id, m.TeacherAssignment.learner_id == submission.learner_id)))
    elif allowed:
        allowed = submission.learner_id == user.id
    if not allowed:
        fail(404, 'NOT_FOUND', 'This submission is not available in your class.')
    return submission


def question_for(db, submission, question_id, require_feedback=True):
    question = db.get(m.QuizQuestion, question_id)
    if not question or question.quiz_id != submission.quiz_id or question_id not in {r['question_id'] for r in submission.responses_json}:
        fail(422, 'INVALID_QUESTION', 'Choose a question from this submission.')
    evaluation = effective_evaluation(db, submission) if require_feedback else None
    if require_feedback and question_id not in {q['question_id'] for q in (evaluation or {}).get('questions', [])
                                                if submission.status == 'graded' or q.get('reviewed')}:
        fail(409, 'FEEDBACK_PENDING', 'Feedback for this question is not available.')
    return question


def review_view(db, submission):
    reviews = list(db.scalars(select(m.TeacherReview).where(m.TeacherReview.submission_id == submission.id)
                             .order_by(m.TeacherReview.created_at, m.TeacherReview.id)))
    disputes = list(db.scalars(select(m.FeedbackDispute).where(m.FeedbackDispute.submission_id == submission.id)
                              .order_by(m.FeedbackDispute.created_at, m.FeedbackDispute.id)))
    resolved = {r.dispute_id: r.id for r in reviews if r.dispute_id}
    fields = ('id', 'question_id', 'teacher_id', 'answer_score', 'reasoning_score', 'feedback', 'misconception',
              'reason', 'dispute_id', 'created_at')
    return dict(submission_id=submission.id, original_evaluation=submission.evaluation_json,
                evaluation=effective_evaluation(db, submission, reviews),
                reviews=[{key: getattr(r, key) for key in fields} for r in reviews],
                disputes=[dict(id=d.id, question_id=d.question_id, reason=d.reason, created_at=d.created_at,
                               status='resolved' if d.id in resolved else 'open', resolution_review_id=resolved.get(d.id))
                          for d in disputes])


def add_review(db, user, submission_id, payload):
    submission = submission_for(db, user, submission_id, lock=True)
    if user.role != 'teacher':
        fail(403, 'FORBIDDEN', 'Only the class teacher can review feedback.')
    question_id = str(payload.question_id)
    question_for(db, submission, question_id, require_feedback=False)
    if payload.dispute_id:
        dispute = db.get(m.FeedbackDispute, str(payload.dispute_id))
        if not dispute or dispute.submission_id != submission.id or dispute.question_id != question_id:
            fail(422, 'INVALID_DISPUTE', 'Choose a dispute for this question and submission.')
        if db.scalar(select(m.TeacherReview.id).where(m.TeacherReview.dispute_id == dispute.id)):
            fail(409, 'DISPUTE_RESOLVED', 'This dispute already has an audited resolution.')
    db.add(m.TeacherReview(submission_id=submission.id, teacher_id=user.id, **payload.model_dump(mode='json')))
    db.flush()
    from app.services.classroom import refresh_course_progress
    refresh_course_progress(db, submission.learner_id)
    return review_view(db, submission)


def add_dispute(db, user, submission_id, payload):
    submission = submission_for(db, user, submission_id, lock=True)
    if user.role != 'learner' or submission.learner_id != user.id:
        fail(403, 'FORBIDDEN', 'Only the student who submitted this answer can dispute it.')
    question_id = str(payload.question_id)
    question_for(db, submission, question_id)
    open_dispute = db.scalar(select(m.FeedbackDispute).where(
        m.FeedbackDispute.submission_id == submission.id, m.FeedbackDispute.question_id == question_id,
        ~select(m.TeacherReview.id).where(m.TeacherReview.dispute_id == m.FeedbackDispute.id).exists()))
    if open_dispute:
        fail(409, 'DISPUTE_OPEN', 'Your concern is already waiting for teacher review.')
    db.add(m.FeedbackDispute(submission_id=submission.id, learner_id=user.id, **payload.model_dump(mode='json')))
    db.flush()
    return review_view(db, submission)
