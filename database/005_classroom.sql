CREATE TABLE class_subjects (
	teacher_id UUID NOT NULL,
	title VARCHAR(120) NOT NULL,
	description TEXT NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (teacher_id, title),
	FOREIGN KEY(teacher_id) REFERENCES users (id)
);

CREATE INDEX ix_class_subjects_teacher_id ON class_subjects (teacher_id);

ALTER TABLE class_subjects ENABLE ROW LEVEL SECURITY;

CREATE TABLE class_courses (
	subject_id UUID NOT NULL,
	title VARCHAR(150) NOT NULL,
	content TEXT NOT NULL,
	position INTEGER NOT NULL,
	concept_id UUID,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(subject_id) REFERENCES class_subjects (id),
	FOREIGN KEY(concept_id) REFERENCES concepts (id)
);

CREATE INDEX ix_class_courses_subject_id ON class_courses (subject_id);

ALTER TABLE class_courses ENABLE ROW LEVEL SECURITY;

CREATE TABLE class_quizzes (
	teacher_id UUID NOT NULL,
	subject_id UUID NOT NULL,
	title VARCHAR(150) NOT NULL,
	status VARCHAR(20) NOT NULL,
	published_at TIMESTAMP WITH TIME ZONE,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(teacher_id) REFERENCES users (id),
	FOREIGN KEY(subject_id) REFERENCES class_subjects (id)
);

CREATE INDEX ix_class_quizzes_teacher_id ON class_quizzes (teacher_id);

ALTER TABLE class_quizzes ENABLE ROW LEVEL SECURITY;

CREATE TABLE quiz_questions (
	quiz_id UUID NOT NULL,
	course_id UUID NOT NULL,
	prompt TEXT NOT NULL,
	expected_answer TEXT NOT NULL,
	rubric TEXT NOT NULL,
	position INTEGER NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(quiz_id) REFERENCES class_quizzes (id),
	FOREIGN KEY(course_id) REFERENCES class_courses (id)
);

CREATE INDEX ix_quiz_questions_quiz_id ON quiz_questions (quiz_id);

ALTER TABLE quiz_questions ENABLE ROW LEVEL SECURITY;

CREATE TABLE quiz_submissions (
	quiz_id UUID NOT NULL,
	learner_id UUID NOT NULL,
	responses_json JSONB NOT NULL,
	evaluation_json JSONB,
	status VARCHAR(20) NOT NULL,
	grading_token VARCHAR(36),
	grading_started_at TIMESTAMP WITH TIME ZONE,
	graded_at TIMESTAMP WITH TIME ZONE,
	error_code VARCHAR(40),
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (quiz_id, learner_id),
	FOREIGN KEY(quiz_id) REFERENCES class_quizzes (id),
	FOREIGN KEY(learner_id) REFERENCES users (id)
);

CREATE INDEX ix_quiz_submissions_quiz_id ON quiz_submissions (quiz_id);

CREATE INDEX ix_quiz_submissions_learner_id ON quiz_submissions (learner_id);

ALTER TABLE quiz_submissions ENABLE ROW LEVEL SECURITY;
