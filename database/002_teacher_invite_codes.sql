CREATE TABLE teacher_invite_codes (
    teacher_id UUID NOT NULL,
    code VARCHAR(80) NOT NULL,
    invited_by_id UUID,
    id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (teacher_id),
    UNIQUE (code),
    FOREIGN KEY (teacher_id) REFERENCES users (id),
    FOREIGN KEY (invited_by_id) REFERENCES users (id)
);
ALTER TABLE teacher_invite_codes ENABLE ROW LEVEL SECURITY;
INSERT INTO teacher_invite_codes (id, created_at, teacher_id, code)
SELECT gen_random_uuid(), now(), id,
       'BM-' || replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '')
FROM users WHERE role = 'teacher';
