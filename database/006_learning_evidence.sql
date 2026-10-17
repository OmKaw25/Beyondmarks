ALTER TABLE users ADD COLUMN data_origin VARCHAR(24) NOT NULL DEFAULT 'unverified';

UPDATE users SET data_origin = 'demo' WHERE is_synthetic = true;

CREATE TABLE delayed_checks (
	learner_id UUID NOT NULL,
	concept_id UUID NOT NULL,
	baseline_attempt_id UUID NOT NULL,
	interval_days INTEGER NOT NULL,
	due_at TIMESTAMP WITH TIME ZONE NOT NULL,
	task_id UUID NOT NULL,
	task_json JSONB NOT NULL,
	answer_json JSONB,
	result_json JSONB,
	completed_at TIMESTAMP WITH TIME ZONE,
	adaptation_attempt_id UUID,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (baseline_attempt_id, interval_days),
	FOREIGN KEY(learner_id) REFERENCES users (id),
	FOREIGN KEY(concept_id) REFERENCES concepts (id),
	FOREIGN KEY(baseline_attempt_id) REFERENCES attempts (id),
	FOREIGN KEY(task_id) REFERENCES independent_tasks (id),
	FOREIGN KEY(adaptation_attempt_id) REFERENCES attempts (id)
);

CREATE INDEX ix_delayed_checks_due_at ON delayed_checks (due_at);

CREATE INDEX ix_delayed_checks_learner_id ON delayed_checks (learner_id);

ALTER TABLE delayed_checks ENABLE ROW LEVEL SECURITY;

CREATE TABLE course_progress (
	learner_id UUID NOT NULL,
	course_id UUID NOT NULL,
	score FLOAT NOT NULL,
	source_submission_id UUID NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (learner_id, course_id),
	FOREIGN KEY(learner_id) REFERENCES users (id),
	FOREIGN KEY(course_id) REFERENCES class_courses (id),
	FOREIGN KEY(source_submission_id) REFERENCES quiz_submissions (id)
);

CREATE INDEX ix_course_progress_learner_id ON course_progress (learner_id);

ALTER TABLE course_progress ENABLE ROW LEVEL SECURITY;

CREATE TABLE feedback_disputes (
	submission_id UUID NOT NULL,
	question_id UUID NOT NULL,
	learner_id UUID NOT NULL,
	reason TEXT NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(submission_id) REFERENCES quiz_submissions (id),
	FOREIGN KEY(question_id) REFERENCES quiz_questions (id),
	FOREIGN KEY(learner_id) REFERENCES users (id)
);

CREATE INDEX ix_feedback_disputes_submission_id ON feedback_disputes (submission_id);

ALTER TABLE feedback_disputes ENABLE ROW LEVEL SECURITY;

CREATE TABLE teacher_reviews (
	submission_id UUID NOT NULL,
	question_id UUID NOT NULL,
	teacher_id UUID NOT NULL,
	answer_score INTEGER NOT NULL,
	reasoning_score INTEGER NOT NULL,
	feedback TEXT NOT NULL,
	misconception TEXT NOT NULL,
	reason TEXT NOT NULL,
	dispute_id UUID,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(submission_id) REFERENCES quiz_submissions (id),
	FOREIGN KEY(question_id) REFERENCES quiz_questions (id),
	FOREIGN KEY(teacher_id) REFERENCES users (id),
	UNIQUE (dispute_id),
	FOREIGN KEY(dispute_id) REFERENCES feedback_disputes (id)
);

CREATE INDEX ix_teacher_reviews_submission_id ON teacher_reviews (submission_id);

ALTER TABLE teacher_reviews ENABLE ROW LEVEL SECURITY;

CREATE INDEX ix_class_quizzes_teacher_page ON class_quizzes (teacher_id, created_at DESC, id);

CREATE INDEX ix_quiz_submissions_quiz_page ON quiz_submissions (quiz_id, created_at DESC, id);

CREATE INDEX ix_auth_sessions_expires_at ON auth_sessions (expires_at);

CREATE INDEX ix_quiz_submissions_learner_status ON quiz_submissions (learner_id, status);
