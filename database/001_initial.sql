CREATE TABLE concepts (
	slug VARCHAR(50) NOT NULL,
	name VARCHAR(100) NOT NULL,
	description TEXT NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (slug)
);

CREATE TABLE users (
	username VARCHAR(32) NOT NULL,
	password_hash TEXT NOT NULL,
	role VARCHAR(16) NOT NULL,
	active BOOLEAN NOT NULL,
	is_synthetic BOOLEAN NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE auth_sessions (
	user_id UUID NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	revoked BOOLEAN NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE exercises (
	concept_id UUID NOT NULL,
	title VARCHAR(150) NOT NULL,
	prompt TEXT NOT NULL,
	code TEXT NOT NULL,
	expected_output TEXT NOT NULL,
	flawed_explanation TEXT NOT NULL,
	active BOOLEAN NOT NULL,
	config JSONB NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(concept_id) REFERENCES concepts (id)
);

CREATE TABLE independent_tasks (
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	concept_id UUID NOT NULL,
	prompt TEXT NOT NULL,
	code TEXT NOT NULL,
	expected_output TEXT NOT NULL,
	explanation_prompt TEXT NOT NULL,
	reasoning_options JSONB NOT NULL,
	correct_tag VARCHAR(80) NOT NULL,
	priority INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(concept_id) REFERENCES concepts (id)
);

CREATE TABLE learner_profiles (
	user_id UUID NOT NULL,
	display_name VARCHAR(80) NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE teacher_assignments (
	teacher_id UUID NOT NULL,
	learner_id UUID NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (teacher_id, learner_id),
	FOREIGN KEY(teacher_id) REFERENCES users (id),
	FOREIGN KEY(learner_id) REFERENCES users (id)
);

CREATE TABLE transfer_tasks (
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	concept_id UUID NOT NULL,
	prompt TEXT NOT NULL,
	code TEXT NOT NULL,
	expected_output TEXT NOT NULL,
	explanation_prompt TEXT NOT NULL,
	reasoning_options JSONB NOT NULL,
	correct_tag VARCHAR(80) NOT NULL,
	priority INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(concept_id) REFERENCES concepts (id)
);

CREATE TABLE attempts (
	learner_id UUID NOT NULL,
	exercise_id UUID NOT NULL,
	stage VARCHAR(30) NOT NULL,
	status VARCHAR(30) NOT NULL,
	is_synthetic BOOLEAN NOT NULL,
	started_at TIMESTAMP WITH TIME ZONE NOT NULL,
	completed_at TIMESTAMP WITH TIME ZONE,
	state JSONB NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(learner_id) REFERENCES users (id),
	FOREIGN KEY(exercise_id) REFERENCES exercises (id)
);

CREATE TABLE explanation_segments (
	exercise_id UUID NOT NULL,
	segment_order INTEGER NOT NULL,
	text TEXT NOT NULL,
	is_flawed BOOLEAN NOT NULL,
	issue_broad_category VARCHAR(40) NOT NULL,
	issue_specific_reason VARCHAR(80) NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(exercise_id) REFERENCES exercises (id)
);

CREATE TABLE follow_ups (
	exercise_id UUID NOT NULL,
	prompt TEXT NOT NULL,
	code TEXT NOT NULL,
	answer_type VARCHAR(30) NOT NULL,
	choices JSONB NOT NULL,
	correct_choice VARCHAR(100) NOT NULL,
	burden_score INTEGER NOT NULL,
	estimated_effort INTEGER NOT NULL,
	priority INTEGER NOT NULL,
	explanation TEXT NOT NULL,
	active BOOLEAN NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(exercise_id) REFERENCES exercises (id)
);

CREATE TABLE hypotheses (
	exercise_id UUID NOT NULL,
	key VARCHAR(80) NOT NULL,
	label VARCHAR(120) NOT NULL,
	description TEXT NOT NULL,
	prior_weight FLOAT NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(exercise_id) REFERENCES exercises (id)
);

CREATE TABLE evidence_rules (
	hypothesis_id UUID NOT NULL,
	evidence_key VARCHAR(120) NOT NULL,
	polarity VARCHAR(20) NOT NULL,
	weight FLOAT NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(hypothesis_id) REFERENCES hypotheses (id)
);

CREATE TABLE follow_up_predictions (
	follow_up_id UUID NOT NULL,
	hypothesis_id UUID NOT NULL,
	predicted_answer_class VARCHAR(100) NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(follow_up_id) REFERENCES follow_ups (id),
	FOREIGN KEY(hypothesis_id) REFERENCES hypotheses (id)
);

CREATE TABLE follow_up_selections (
	attempt_id UUID NOT NULL,
	follow_up_id UUID,
	divergence_score FLOAT NOT NULL,
	burden_penalty INTEGER NOT NULL,
	final_score FLOAT NOT NULL,
	rationale TEXT NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(attempt_id) REFERENCES attempts (id),
	FOREIGN KEY(follow_up_id) REFERENCES follow_ups (id)
);

CREATE TABLE hypothesis_assessments (
	attempt_id UUID NOT NULL,
	hypothesis_id UUID NOT NULL,
	score FLOAT NOT NULL,
	confidence_label VARCHAR(20) NOT NULL,
	evidence_summary JSONB NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(attempt_id) REFERENCES attempts (id),
	FOREIGN KEY(hypothesis_id) REFERENCES hypotheses (id)
);

CREATE TABLE independent_attempts (
	task_id UUID NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	learner_id UUID NOT NULL,
	attempt_id UUID NOT NULL,
	answer TEXT NOT NULL,
	explanation TEXT NOT NULL,
	correct BOOLEAN NOT NULL,
	evidence_json JSONB NOT NULL,
	completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(task_id) REFERENCES independent_tasks (id),
	FOREIGN KEY(learner_id) REFERENCES users (id),
	FOREIGN KEY(attempt_id) REFERENCES attempts (id)
);

CREATE TABLE learner_challenges (
	attempt_id UUID NOT NULL,
	system_hypothesis_id UUID,
	alternative_hypothesis_id UUID NOT NULL,
	learner_reason TEXT NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(attempt_id) REFERENCES attempts (id),
	FOREIGN KEY(system_hypothesis_id) REFERENCES hypotheses (id),
	FOREIGN KEY(alternative_hypothesis_id) REFERENCES hypotheses (id)
);

CREATE TABLE learner_evidence (
	attempt_id UUID NOT NULL,
	evidence_key VARCHAR(120) NOT NULL,
	value_json JSONB NOT NULL,
	source VARCHAR(30) NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(attempt_id) REFERENCES attempts (id)
);

CREATE TABLE retention_checks (
	learner_id UUID NOT NULL,
	concept_id UUID NOT NULL,
	baseline_attempt_id UUID NOT NULL,
	check_date TIMESTAMP WITH TIME ZONE NOT NULL,
	is_synthetic BOOLEAN NOT NULL,
	outcome VARCHAR(10) NOT NULL,
	prompt TEXT NOT NULL,
	code TEXT NOT NULL,
	expected_output TEXT NOT NULL,
	explanation TEXT NOT NULL,
	adaptation_required BOOLEAN NOT NULL,
	adaptation_attempt_id UUID,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(learner_id) REFERENCES users (id),
	FOREIGN KEY(concept_id) REFERENCES concepts (id),
	FOREIGN KEY(baseline_attempt_id) REFERENCES attempts (id),
	FOREIGN KEY(adaptation_attempt_id) REFERENCES attempts (id)
);

CREATE TABLE support_modules (
	hypothesis_id UUID,
	exercise_id UUID NOT NULL,
	title VARCHAR(150) NOT NULL,
	explanation TEXT NOT NULL,
	worked_example TEXT NOT NULL,
	prediction_prompt TEXT NOT NULL,
	choices_json JSONB NOT NULL,
	correct_choice VARCHAR(100) NOT NULL,
	feedback_correct TEXT NOT NULL,
	feedback_incorrect TEXT NOT NULL,
	priority INTEGER NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(hypothesis_id) REFERENCES hypotheses (id),
	FOREIGN KEY(exercise_id) REFERENCES exercises (id)
);

CREATE TABLE transfer_attempts (
	transfer_task_id UUID NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	learner_id UUID NOT NULL,
	attempt_id UUID NOT NULL,
	answer TEXT NOT NULL,
	explanation TEXT NOT NULL,
	correct BOOLEAN NOT NULL,
	evidence_json JSONB NOT NULL,
	completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(transfer_task_id) REFERENCES transfer_tasks (id),
	FOREIGN KEY(learner_id) REFERENCES users (id),
	FOREIGN KEY(attempt_id) REFERENCES attempts (id)
);

CREATE TABLE adaptation_events (
	learner_id UUID NOT NULL,
	attempt_id UUID NOT NULL,
	source_check_id UUID,
	old_assessment_json JSONB NOT NULL,
	new_assessment_json JSONB NOT NULL,
	support_module_id UUID,
	verification_task_id UUID,
	reason TEXT NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(learner_id) REFERENCES users (id),
	FOREIGN KEY(attempt_id) REFERENCES attempts (id),
	FOREIGN KEY(source_check_id) REFERENCES retention_checks (id),
	FOREIGN KEY(support_module_id) REFERENCES support_modules (id),
	FOREIGN KEY(verification_task_id) REFERENCES independent_tasks (id)
);

CREATE TABLE support_attempts (
	attempt_id UUID NOT NULL,
	support_module_id UUID NOT NULL,
	selected_choice VARCHAR(100) NOT NULL,
	correct BOOLEAN NOT NULL,
	completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(attempt_id) REFERENCES attempts (id),
	FOREIGN KEY(support_module_id) REFERENCES support_modules (id)
);

CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id);

CREATE INDEX ix_exercises_concept_id ON exercises (concept_id);

CREATE INDEX ix_independent_tasks_concept_id ON independent_tasks (concept_id);

CREATE INDEX ix_teacher_assignments_learner_id ON teacher_assignments (learner_id);

CREATE INDEX ix_teacher_assignments_teacher_id ON teacher_assignments (teacher_id);

CREATE INDEX ix_transfer_tasks_concept_id ON transfer_tasks (concept_id);

CREATE INDEX ix_attempts_exercise_id ON attempts (exercise_id);

CREATE INDEX ix_attempts_learner_id ON attempts (learner_id);

CREATE INDEX ix_explanation_segments_exercise_id ON explanation_segments (exercise_id);

CREATE INDEX ix_follow_ups_exercise_id ON follow_ups (exercise_id);

CREATE INDEX ix_hypotheses_exercise_id ON hypotheses (exercise_id);

CREATE INDEX ix_evidence_rules_hypothesis_id ON evidence_rules (hypothesis_id);

CREATE INDEX ix_follow_up_predictions_follow_up_id ON follow_up_predictions (follow_up_id);

CREATE INDEX ix_follow_up_predictions_hypothesis_id ON follow_up_predictions (hypothesis_id);

CREATE INDEX ix_follow_up_selections_attempt_id ON follow_up_selections (attempt_id);

CREATE INDEX ix_hypothesis_assessments_attempt_id ON hypothesis_assessments (attempt_id);

CREATE INDEX ix_hypothesis_assessments_hypothesis_id ON hypothesis_assessments (hypothesis_id);

CREATE INDEX ix_independent_attempts_attempt_id ON independent_attempts (attempt_id);

CREATE INDEX ix_independent_attempts_learner_id ON independent_attempts (learner_id);

CREATE INDEX ix_learner_challenges_attempt_id ON learner_challenges (attempt_id);

CREATE INDEX ix_learner_evidence_attempt_id ON learner_evidence (attempt_id);

CREATE INDEX ix_retention_checks_check_date ON retention_checks (check_date);

CREATE INDEX ix_retention_checks_concept_id ON retention_checks (concept_id);

CREATE INDEX ix_retention_checks_learner_id ON retention_checks (learner_id);

CREATE INDEX ix_support_modules_exercise_id ON support_modules (exercise_id);

CREATE INDEX ix_support_modules_hypothesis_id ON support_modules (hypothesis_id);

CREATE INDEX ix_transfer_attempts_attempt_id ON transfer_attempts (attempt_id);

CREATE INDEX ix_transfer_attempts_learner_id ON transfer_attempts (learner_id);

CREATE INDEX ix_adaptation_events_attempt_id ON adaptation_events (attempt_id);

CREATE INDEX ix_adaptation_events_learner_id ON adaptation_events (learner_id);

CREATE INDEX ix_support_attempts_attempt_id ON support_attempts (attempt_id);

ALTER TABLE adaptation_events ENABLE ROW LEVEL SECURITY;

ALTER TABLE attempts ENABLE ROW LEVEL SECURITY;

ALTER TABLE auth_sessions ENABLE ROW LEVEL SECURITY;

ALTER TABLE concepts ENABLE ROW LEVEL SECURITY;

ALTER TABLE evidence_rules ENABLE ROW LEVEL SECURITY;

ALTER TABLE exercises ENABLE ROW LEVEL SECURITY;

ALTER TABLE explanation_segments ENABLE ROW LEVEL SECURITY;

ALTER TABLE follow_up_predictions ENABLE ROW LEVEL SECURITY;

ALTER TABLE follow_up_selections ENABLE ROW LEVEL SECURITY;

ALTER TABLE follow_ups ENABLE ROW LEVEL SECURITY;

ALTER TABLE hypotheses ENABLE ROW LEVEL SECURITY;

ALTER TABLE hypothesis_assessments ENABLE ROW LEVEL SECURITY;

ALTER TABLE independent_attempts ENABLE ROW LEVEL SECURITY;

ALTER TABLE independent_tasks ENABLE ROW LEVEL SECURITY;

ALTER TABLE learner_challenges ENABLE ROW LEVEL SECURITY;

ALTER TABLE learner_evidence ENABLE ROW LEVEL SECURITY;

ALTER TABLE learner_profiles ENABLE ROW LEVEL SECURITY;

ALTER TABLE retention_checks ENABLE ROW LEVEL SECURITY;

ALTER TABLE support_attempts ENABLE ROW LEVEL SECURITY;

ALTER TABLE support_modules ENABLE ROW LEVEL SECURITY;

ALTER TABLE teacher_assignments ENABLE ROW LEVEL SECURITY;

ALTER TABLE transfer_attempts ENABLE ROW LEVEL SECURITY;

ALTER TABLE transfer_tasks ENABLE ROW LEVEL SECURITY;

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
