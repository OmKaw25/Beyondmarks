# Teacher classrooms, quizzes, and learning priorities

Requested by Om on 2026-10-17. Teachers author subjects, topics, lessons, quiz questions, and answer keys. Gemini's free tier is selected for written-reasoning feedback; live grading requires a configured API key.

## Enrollment

Each teacher owns two distinct reusable codes: the existing teacher referral code and a new student enrollment code. Teacher referrals create a separate teacher workspace with its own two codes. Student signup requires the student code and atomically creates a TeacherAssignment to that teacher. The shared teacher_id connects the class; student user IDs remain unique. Existing accounts, codes, assignments, and evidence remain intact. Student codes cannot create teachers, and teacher codes cannot enroll students. Only the owning teacher can retrieve either code.

## Subjects and quizzes

A teacher owns subjects containing courses/topics with teacher-written lesson text. Each teacher starts with Basic programming and the three existing programming topics, connected to the authored investigations. Teachers add subjects such as Basic Maths and write its courses. Enrolled learners see only their teachers' subjects, lessons, and published quizzes. Teachers create a quiz with a title, subject, and questions tied to that subject's courses. Each question has a prompt, expected answer, and reasoning guidance. Draft quizzes stay private; publishing freezes the questions and answer key. This supplies fresh teacher-authored questions rather than repeating the fixed investigations.

Learners submit an answer and written reasoning for every question once per quiz. Answers are saved before grading; network failures never lose work. Answer keys and rubric are excluded from student quiz payloads before submission. A completed quiz is reviewable and cannot be submitted again. Only the owning teacher can see all submissions to a quiz.

## AI feedback and recommendations

One server-side Gemini request grades a complete submission against the teacher's answer keys and reasoning guidance. Send no account names or IDs; opaque question IDs only. Require structured, bounded answer and reasoning scores (0–100), feedback, and topic-specific misconceptions. Treat learner text as data, never instructions. Validate response shape and exact question membership. Store model identity and feedback separately from immutable student responses. AI feedback is labelled as AI feedback for teacher review, not a certain diagnosis.

If no key, quota, timeout, malformed response, or provider failure occurs, persist the submission as awaiting feedback, show that state, and offer an explicit retry. Never substitute fabricated AI grades or infer failure from missing grades. Concurrent/repeated grading is protected by a database claim with an expiring lease; no database lock is held during the provider request.

After grading, compute each course's average answer/reasoning score from its latest graded quiz. Recommend assessed courses below 60% first (lowest score first), then unassessed courses in teacher order, then stronger assessed courses. The 60% cutoff is a product prioritization rule, not a validated ability measure. Questions flagged as ambiguous by the AI are excluded from course scoring. Show the supporting topic score and explain why it is recommended. Programming investigations use the same course-to-concept link to reorder their cards. Scores are evidence from quizzes, not measured ability or a leaderboard.

Live provider verification succeeded with gemini-3.5-flash-lite. The older 2.5 Flash-Lite model was listed by discovery but rejected for new users; the provider recommended the current model. Pricing documentation lists free-tier input/output for the selected model. Keys remain in the gitignored backend environment, never browser bundles.

## Implementation and checks

1. Add student codes, signup enrollment, and teacher code panels; test reuse, role separation, automatic assignment, and cross-class access.
2. Add subjects/courses and draft/published quizzes with ownership-checked APIs and teacher/student screens. Test publishing, hidden answers, immutable submissions, and access boundaries.
3. Add Gemini grading, saved pending states, retry claims, teacher results, and recommendation ordering. Test grading validation/failure paths using transport fixtures only; verify real provider behavior when the key is configured.
4. Apply additive database migrations, backfill existing teacher classrooms, and verify enrollment and quiz browser workflows. Reuse existing design tokens and form components.
