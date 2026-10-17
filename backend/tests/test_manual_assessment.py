"""Teacher assessment remains usable during AI outages without inventing grades."""
from copy import deepcopy
import pytest
from sqlalchemy.orm import Session
from app import models as m
from app.errors import AppError
from app.schemas.learning_evidence import ReviewInput, DisputeInput
from app.services import feedback_review as reviews
from app.services.classroom import course_scores, submission_view, overview
from app.services.quiz_submissions import evaluate_submission
from test_learning_evidence import graded_submission, user

pytestmark = pytest.mark.integration


def pending(db):
    teacher, learner, first, submission = graded_submission(db)
    second = m.QuizQuestion(quiz_id=first.quiz_id, course_id=first.course_id, position=1,
                           prompt='Another explanation?', expected_answer='Evidence', rubric='')
    db.add(second); db.flush()
    submission.responses_json = submission.responses_json + [dict(question_id=second.id, answer='Evidence', reasoning='It supports the claim.')]
    submission.status = 'pending'; submission.evaluation_json = None; submission.error_code = 'QUOTA_LIMIT'
    db.flush()
    return teacher, learner, first, second, submission


def assessment(question, score=80):
    return ReviewInput(question_id=question.id, answer_score=score, reasoning_score=score,
                       feedback='Your evidence supports the answer.', reason='Teacher assessed the saved response directly.')


def test_partial_and_complete_manual_assessment_without_ai(integration_engine):
    with Session(integration_engine, expire_on_commit=False) as db:
        teacher, learner, first, second, submission = pending(db)
        original_responses = deepcopy(submission.responses_json)
        assert overview(db, learner)['quizzes_page']['total'] == 1  # Quiz count must not become response count.
        assert overview(db, learner)['quizzes'][0]['assessment'] == {'status': 'pending', 'assessed_questions': 0, 'total_questions': 2}
        with pytest.raises(AppError) as error:
            reviews.add_dispute(db, learner, submission.id, DisputeInput(question_id=first.id, reason='No feedback yet.'))
        assert error.value.code == 'FEEDBACK_PENDING'
        result = reviews.add_review(db, teacher, submission.id, assessment(first))
        assert result['original_evaluation'] is None
        assert result['evaluation']['source'] == 'teacher'
        assert len(result['evaluation']['questions']) == 1
        assert course_scores(db, learner.id)[first.course_id] == 80  # Unassessed second answer is not zero.
        view = submission_view(db, submission)
        assert view['assessment'] == {'status': 'partial', 'assessed_questions': 1, 'total_questions': 2}
        assert overview(db, learner)['quizzes'][0]['assessment'] == view['assessment']
        assert submission.status == 'pending' and submission.evaluation_json is None
        assert reviews.add_dispute(db, learner, submission.id, DisputeInput(question_id=first.id, reason='Please reconsider the reasoning.'))['disputes']
        reviews.add_review(db, teacher, submission.id, assessment(second, 40))
        assert submission_view(db, submission)['assessment']['status'] == 'complete'
        assert overview(db, learner)['quizzes'][0]['assessment'] == {'status': 'complete', 'assessed_questions': 2, 'total_questions': 2}
        assert course_scores(db, learner.id)[first.course_id] == 60
        assert submission.responses_json == original_responses
        db.rollback()


def test_manual_assessment_scope_and_response_membership(integration_engine):
    with Session(integration_engine, expire_on_commit=False) as db:
        teacher, learner, first, second, submission = pending(db)
        for outsider in [user(db, 'teacher'), user(db)]:
            with pytest.raises(AppError) as error:
                reviews.add_review(db, outsider, submission.id, assessment(first))
            assert error.value.status == 404
        with pytest.raises(AppError) as error:
            reviews.add_review(db, learner, submission.id, assessment(first))
        assert error.value.status == 403
        submission.responses_json = submission.responses_json[:1]
        with pytest.raises(AppError) as error:
            reviews.add_review(db, teacher, submission.id, assessment(second))
        assert error.value.code == 'INVALID_QUESTION'
        db.rollback()


def test_ai_finishing_after_teacher_review_keeps_teacher_scores(integration_engine, monkeypatch):
    with Session(integration_engine, expire_on_commit=False) as db:
        teacher, learner, first, second, submission = pending(db)
        db.commit()
        def delayed_ai(questions):
            # Only the external transport is simulated; assessment persists in another real transaction.
            with Session(integration_engine, expire_on_commit=False) as teacher_db:
                reviews.add_review(teacher_db, teacher_db.get(m.User, teacher.id), submission.id, assessment(first, 90))
                teacher_db.commit()
            return {'source': 'test transport', 'model': 'fixture', 'questions': [dict(question_id=q['question_id'],
                answer_score=20, reasoning_score=20, feedback='Check your reasoning.', misconception='', needs_review=False) for q in questions]}
        monkeypatch.setattr('app.services.quiz_submissions.grade_questions', delayed_ai)
        evaluate_submission(db, learner, submission.id)
        result = reviews.review_view(db, submission)
        assert result['original_evaluation']['questions'][0]['answer_score'] == 20
        assert result['evaluation']['questions'][0]['answer_score'] == 90
        assert result['evaluation']['questions'][1]['answer_score'] == 20
        assert course_scores(db, learner.id)[first.course_id] == 55
        assert submission_view(db, submission)['assessment']['status'] == 'complete'
        assert overview(db, learner)['quizzes'][0]['assessment'] == {'status': 'complete', 'assessed_questions': 2, 'total_questions': 2}
