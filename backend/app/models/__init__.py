"""PostgreSQL storage. Evidence and assessments are append-only in application services."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

JSON_TYPE = JSON().with_variant(JSONB(), 'postgresql')


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class User(Record, Base):
    __tablename__ = 'users'
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    data_origin: Mapped[str] = mapped_column(String(24), default='unverified', server_default='unverified')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class LearnerProfile(Record, Base):
    __tablename__ = 'learner_profiles'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True)
    display_name: Mapped[str] = mapped_column(String(80))


class AuthSession(Record, Base):
    __tablename__ = 'auth_sessions'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class TeacherAssignment(Record, Base):
    __tablename__ = 'teacher_assignments'
    __table_args__ = (UniqueConstraint('teacher_id', 'learner_id'),)
    teacher_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)


class TeacherInviteCode(Record, Base):
    __tablename__ = 'teacher_invite_codes'
    teacher_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True)
    code: Mapped[str] = mapped_column(String(80), unique=True)
    student_code: Mapped[str] = mapped_column(String(80), unique=True)
    invited_by_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)


class ClassSubject(Record, Base):
    __tablename__ = 'class_subjects'
    __table_args__ = (UniqueConstraint('teacher_id', 'title'),)
    teacher_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default='')


class ClassCourse(Record, Base):
    __tablename__ = 'class_courses'
    subject_id: Mapped[str] = mapped_column(ForeignKey('class_subjects.id'), index=True)
    title: Mapped[str] = mapped_column(String(150))
    content: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    concept_id: Mapped[str | None] = mapped_column(ForeignKey('concepts.id'), nullable=True)


class ClassQuiz(Record, Base):
    __tablename__ = 'class_quizzes'
    teacher_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey('class_subjects.id'))
    title: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(20), default='draft')
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class QuizQuestion(Record, Base):
    __tablename__ = 'quiz_questions'
    quiz_id: Mapped[str] = mapped_column(ForeignKey('class_quizzes.id'), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey('class_courses.id'))
    prompt: Mapped[str] = mapped_column(Text)
    expected_answer: Mapped[str] = mapped_column(Text)
    rubric: Mapped[str] = mapped_column(Text, default='')
    position: Mapped[int] = mapped_column(Integer)


class QuizSubmission(Record, Base):
    __tablename__ = 'quiz_submissions'
    __table_args__ = (UniqueConstraint('quiz_id', 'learner_id'),)
    quiz_id: Mapped[str] = mapped_column(ForeignKey('class_quizzes.id'), index=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    responses_json: Mapped[list] = mapped_column(JSON_TYPE)
    evaluation_json: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    grading_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    grading_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)


class Concept(Record, Base):
    __tablename__ = 'concepts'
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)


class Exercise(Record, Base):
    __tablename__ = 'exercises'
    concept_id: Mapped[str] = mapped_column(ForeignKey('concepts.id'), index=True)
    title: Mapped[str] = mapped_column(String(150))
    prompt: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    flawed_explanation: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)


class ExplanationSegment(Record, Base):
    __tablename__ = 'explanation_segments'
    exercise_id: Mapped[str] = mapped_column(ForeignKey('exercises.id'), index=True)
    segment_order: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    is_flawed: Mapped[bool] = mapped_column(Boolean)
    issue_broad_category: Mapped[str] = mapped_column(String(40))
    issue_specific_reason: Mapped[str] = mapped_column(String(80))


class Hypothesis(Record, Base):
    __tablename__ = 'hypotheses'
    exercise_id: Mapped[str] = mapped_column(ForeignKey('exercises.id'), index=True)
    key: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    prior_weight: Mapped[float] = mapped_column(Float, default=1)


class EvidenceRule(Record, Base):
    __tablename__ = 'evidence_rules'
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey('hypotheses.id'), index=True)
    evidence_key: Mapped[str] = mapped_column(String(120))
    polarity: Mapped[str] = mapped_column(String(20))
    weight: Mapped[float] = mapped_column(Float)


class FollowUp(Record, Base):
    __tablename__ = 'follow_ups'
    exercise_id: Mapped[str] = mapped_column(ForeignKey('exercises.id'), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text, default='')
    answer_type: Mapped[str] = mapped_column(String(30), default='choice')
    choices: Mapped[list] = mapped_column(JSON_TYPE)
    correct_choice: Mapped[str] = mapped_column(String(100))
    burden_score: Mapped[int] = mapped_column(Integer, default=0)
    estimated_effort: Mapped[int] = mapped_column(Integer, default=10)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    explanation: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class FollowUpPrediction(Record, Base):
    __tablename__ = 'follow_up_predictions'
    follow_up_id: Mapped[str] = mapped_column(ForeignKey('follow_ups.id'), index=True)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey('hypotheses.id'), index=True)
    predicted_answer_class: Mapped[str] = mapped_column(String(100))


class Attempt(Record, Base):
    __tablename__ = 'attempts'
    learner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey('exercises.id'), index=True)
    stage: Mapped[str] = mapped_column(String(30), default='investigate')
    status: Mapped[str] = mapped_column(String(30), default='active')
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    state: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)


class LearnerEvidence(Record, Base):
    __tablename__ = 'learner_evidence'
    attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'), index=True)
    evidence_key: Mapped[str] = mapped_column(String(120))
    value_json: Mapped[dict] = mapped_column(JSON_TYPE)
    source: Mapped[str] = mapped_column(String(30))


class HypothesisAssessment(Record, Base):
    __tablename__ = 'hypothesis_assessments'
    attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'), index=True)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey('hypotheses.id'), index=True)
    score: Mapped[float] = mapped_column(Float)
    confidence_label: Mapped[str] = mapped_column(String(20))
    evidence_summary: Mapped[dict] = mapped_column(JSON_TYPE)


class LearnerChallenge(Record, Base):
    __tablename__ = 'learner_challenges'
    attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'), index=True)
    system_hypothesis_id: Mapped[str | None] = mapped_column(ForeignKey('hypotheses.id'))
    alternative_hypothesis_id: Mapped[str] = mapped_column(ForeignKey('hypotheses.id'))
    learner_reason: Mapped[str] = mapped_column(Text, default='')


class FollowUpSelection(Record, Base):
    __tablename__ = 'follow_up_selections'
    attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'), index=True)
    follow_up_id: Mapped[str | None] = mapped_column(ForeignKey('follow_ups.id'))
    divergence_score: Mapped[float] = mapped_column(Float)
    burden_penalty: Mapped[int] = mapped_column(Integer)
    final_score: Mapped[float] = mapped_column(Float)
    rationale: Mapped[str] = mapped_column(Text)


class SupportModule(Record, Base):
    __tablename__ = 'support_modules'
    hypothesis_id: Mapped[str | None] = mapped_column(ForeignKey('hypotheses.id'), index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey('exercises.id'), index=True)
    title: Mapped[str] = mapped_column(String(150))
    explanation: Mapped[str] = mapped_column(Text)
    worked_example: Mapped[str] = mapped_column(Text)
    prediction_prompt: Mapped[str] = mapped_column(Text)
    choices_json: Mapped[list] = mapped_column(JSON_TYPE)
    correct_choice: Mapped[str] = mapped_column(String(100))
    feedback_correct: Mapped[str] = mapped_column(Text)
    feedback_incorrect: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0)


class SupportAttempt(Record, Base):
    __tablename__ = 'support_attempts'
    attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'), index=True)
    support_module_id: Mapped[str] = mapped_column(ForeignKey('support_modules.id'))
    selected_choice: Mapped[str] = mapped_column(String(100))
    correct: Mapped[bool] = mapped_column(Boolean)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TaskFields:
    phase: Mapped[str] = mapped_column(String(20), default='independent')
    interaction_json: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    concept_id: Mapped[str] = mapped_column(ForeignKey('concepts.id'), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    explanation_prompt: Mapped[str] = mapped_column(Text)
    reasoning_options: Mapped[list] = mapped_column(JSON_TYPE)
    correct_tag: Mapped[str] = mapped_column(String(80))
    priority: Mapped[int] = mapped_column(Integer, default=0)


class TransferTask(Record, TaskFields, Base):
    __tablename__ = 'transfer_tasks'


class IndependentTask(Record, TaskFields, Base):
    __tablename__ = 'independent_tasks'


class TaskAttemptFields:
    learner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'), index=True)
    answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    correct: Mapped[bool] = mapped_column(Boolean)
    evidence_json: Mapped[dict] = mapped_column(JSON_TYPE)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TransferAttempt(Record, TaskAttemptFields, Base):
    __tablename__ = 'transfer_attempts'
    transfer_task_id: Mapped[str] = mapped_column(ForeignKey('transfer_tasks.id'))


class IndependentAttempt(Record, TaskAttemptFields, Base):
    __tablename__ = 'independent_attempts'
    task_id: Mapped[str] = mapped_column(ForeignKey('independent_tasks.id'))


class RetentionCheck(Record, Base):
    __tablename__ = 'retention_checks'
    learner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey('concepts.id'), index=True)
    baseline_attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'))
    check_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    outcome: Mapped[str] = mapped_column(String(10))
    prompt: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    adaptation_required: Mapped[bool] = mapped_column(Boolean)
    adaptation_attempt_id: Mapped[str | None] = mapped_column(ForeignKey('attempts.id'))


class AdaptationEvent(Record, Base):
    __tablename__ = 'adaptation_events'
    learner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'), index=True)
    source_check_id: Mapped[str | None] = mapped_column(ForeignKey('retention_checks.id'))
    old_assessment_json: Mapped[dict] = mapped_column(JSON_TYPE)
    new_assessment_json: Mapped[dict] = mapped_column(JSON_TYPE)
    support_module_id: Mapped[str | None] = mapped_column(ForeignKey('support_modules.id'))
    verification_task_id: Mapped[str | None] = mapped_column(ForeignKey('independent_tasks.id'))
    reason: Mapped[str] = mapped_column(Text)


class DelayedCheck(Record, Base):
    """Real scheduled evidence; deliberately separate from synthetic retention history."""
    __tablename__ = 'delayed_checks'
    __table_args__ = (UniqueConstraint('baseline_attempt_id', 'interval_days'),)
    learner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey('concepts.id'))
    baseline_attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'))
    interval_days: Mapped[int] = mapped_column(Integer)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey('independent_tasks.id'))
    task_json: Mapped[dict] = mapped_column(JSON_TYPE)
    answer_json: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    adaptation_attempt_id: Mapped[str | None] = mapped_column(ForeignKey('attempts.id'), nullable=True)


class FeedbackDispute(Record, Base):
    __tablename__ = 'feedback_disputes'
    submission_id: Mapped[str] = mapped_column(ForeignKey('quiz_submissions.id'), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey('quiz_questions.id'))
    learner_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    reason: Mapped[str] = mapped_column(Text)


class TeacherReview(Record, Base):
    __tablename__ = 'teacher_reviews'
    submission_id: Mapped[str] = mapped_column(ForeignKey('quiz_submissions.id'), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey('quiz_questions.id'))
    teacher_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    answer_score: Mapped[int] = mapped_column(Integer)
    reasoning_score: Mapped[int] = mapped_column(Integer)
    feedback: Mapped[str] = mapped_column(Text)
    misconception: Mapped[str] = mapped_column(Text, default='')
    reason: Mapped[str] = mapped_column(Text)
    dispute_id: Mapped[str | None] = mapped_column(ForeignKey('feedback_disputes.id'), nullable=True, unique=True)


class CourseProgress(Record, Base):
    __tablename__ = 'course_progress'
    __table_args__ = (UniqueConstraint('learner_id', 'course_id'),)
    learner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey('class_courses.id'))
    score: Mapped[float] = mapped_column(Float)
    source_submission_id: Mapped[str] = mapped_column(ForeignKey('quiz_submissions.id'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


Index('ix_class_quizzes_teacher_page', ClassQuiz.teacher_id, ClassQuiz.created_at.desc(), ClassQuiz.id)
Index('ix_quiz_submissions_quiz_page', QuizSubmission.quiz_id, QuizSubmission.created_at.desc(), QuizSubmission.id)
Index('ix_auth_sessions_expires_at', AuthSession.expires_at)
Index('ix_quiz_submissions_learner_status', QuizSubmission.learner_id, QuizSubmission.status)
Index('ix_attempts_learner_real_latest', Attempt.learner_id, Attempt.exercise_id,
      Attempt.created_at.desc(), Attempt.id.desc(), postgresql_where=Attempt.is_synthetic == False)
Index('ix_delayed_checks_learner_due', DelayedCheck.learner_id, DelayedCheck.due_at, DelayedCheck.id)
