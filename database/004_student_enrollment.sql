ALTER TABLE teacher_invite_codes ADD COLUMN student_code VARCHAR(80);
UPDATE teacher_invite_codes SET student_code = 'BMS-' || replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');
ALTER TABLE teacher_invite_codes ALTER COLUMN student_code SET NOT NULL;
ALTER TABLE teacher_invite_codes ADD CONSTRAINT uq_student_invite_code UNIQUE (student_code);
