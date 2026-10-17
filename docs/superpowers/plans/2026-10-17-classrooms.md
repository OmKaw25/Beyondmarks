# Classroom Implementation Plan

> Execute inline using superpowers:executing-plans. User has requested implementation and selected teacher-authored lessons and a free AI provider.

**Goal:** Enroll students under teachers, deliver class subjects and quizzes, and prioritize courses using quiz feedback.
**Architecture:** Extend TeacherAssignment, add teacher-owned subjects/courses/quizzes and immutable submissions, call Gemini only from the backend.
**Tech Stack:** Existing Next.js, FastAPI, SQLAlchemy, PostgreSQL, httpx.
**Spec:** docs/classroom-design.md

- [x] Enrollment: migration 0004 adds student_code to teacher_invite_codes; extend invitation service, signup, teacher panels, and integration tests.
- [x] Classroom content: migration 0005 adds subjects, courses, quizzes, questions, and submissions; separate classroom service/router and scoped APIs.
- [x] Quiz evaluation: Gemini service validates structured feedback; submission service preserves responses and handles retry claims. No key means awaiting feedback.
- [x] UI: teacher classroom authoring, course reading, learner quiz submission, results and recommendation cards; existing tokens, responsive forms.
- [x] Verification: focused backend tests, frontend typecheck, real database integration, browser enrollment/quiz paths and live Gemini check once configured.

Review focus: codes used for the wrong role; cross-teacher question/course IDs; unpublished keys leaking to learners; duplicate/concurrent submissions; provider failure after answers have been saved.

Final review: fixed controlled-form recovery, stale ORM grading claims, and malformed provider envelopes. Added regression coverage. Browser verification passed all 11 scenarios (10 in the full run plus the corrected named-learner selector check); frontend typecheck and lint passed. Live Gemini feedback verified on a three-topic quiz and recommendation ordering checked. See docs/environment-rca.md for resolved model access, screenshot overflow, test selector, and interrupted database fixture setup.

Ruling: use a shared teacher_id through TeacherAssignment rather than reusing student identifiers. Existing memberships remain intact. New referrals create independent teacher classrooms. Published content is immutable; draft edits replace only unpublished question definitions.

Final backend run: 49 passed in 161.98 seconds, including PostgreSQL ownership, automatic enrollment, quiz immutability, saved pending answers, stale grading lease protection, and course recommendation ordering. Migration 0005 is applied; existing teachers have Basic programming courses. Local FastAPI and Next.js remain running. No deployment or push was performed.
