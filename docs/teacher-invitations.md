# Reusable teacher codes — user-directed update, 2026-10-17

Om requested one mock teacher account and a unique code for each teacher, required only when creating another teacher account. Om clarified that the code must be reusable and can register any number of teachers.

The existing labelled `teacher_demo` is the mock account. Each teacher owns a cryptographically random invitation code. A teacher can view and copy only their own code on their dashboard. Signup validates a supplied code against an active teacher, creates a teacher account, and gives the new teacher a different reusable code. Regular login uses only username/password and reads the stored role. Learner signup requires no invitation. Sharing an invitation never assigns learners or grants access to the inviter's learner records.

A versioned additive migration stores teacher codes with unique owner/code constraints and optional inviter attribution. It provisions codes for existing teachers without altering their passwords or evidence. Codes are intentionally retrievable by their owner, are stored in the protected database, and are omitted from learner, timeline, and ordinary auth responses. The obsolete shared `TEACHER_INVITE_CODE` setting no longer authorizes signup.

Verification: missing/incorrect codes fail; the same valid code creates two distinct teachers; each new code differs; learner access to the code endpoint fails; codes from inactive teachers fail; teacher login requires no code; ordinary learner login and assignments still work.
