-- Additive lookup indexes. Existing users, enrollment and evidence are unchanged.
-- Matches the learner dashboard's DISTINCT ON and latest real attempt lookup.
CREATE INDEX ix_attempts_learner_real_latest
    ON attempts (learner_id, exercise_id, created_at DESC, id DESC)
    WHERE is_synthetic = false;

-- Matches each learner's delayed-check listing and chronological ordering.
CREATE INDEX ix_delayed_checks_learner_due
    ON delayed_checks (learner_id, due_at, id);
