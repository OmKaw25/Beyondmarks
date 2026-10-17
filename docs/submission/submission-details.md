# Beyond Marks - submission details

**Project:** Beyond Marks - Understanding Learner Reasoning and Enabling Lasting Learning

**Track:** Learning

**Repository:** https://github.com/OmKaw25/Beyondmarks

**Release and downloadable files:** https://github.com/OmKaw25/Beyondmarks/releases/tag/v1.2.0-hackathon

## Problem statement

Build a learning system that distinguishes understanding from a correct or incorrect answer. It should collect reasoning and learner context, retain competing explanations for a mistake, and select a useful next interaction without repeatedly testing the same thing. Learners must be able to question the interpretation and ask for help. Teachers need evidence they can review and correct. The system should verify understanding in a changed situation, through independent work and after a real delay, then revise support when later evidence contradicts an earlier conclusion.

## Solution summary

Beyond Marks combines a structured learning investigation with teacher-led classrooms. Students examine flawed explanations, share reasoning and optional context, inspect tentative interpretations, and answer one informative follow-up. Interactive support leads to changed-context transfer, independent work and reflection. Failed checks produce fresh examples and verification tasks. Completed eligible investigations schedule real 7-day and 30-day checks, with early access blocked by the server.

Teachers enroll students through reusable class codes, author subjects and lessons, publish quizzes and review written reasoning. AI quiz feedback can be challenged by students and corrected by teachers while preserving the original assessment. Teachers can assess saved responses even during an AI outage; partial work is not zero-filled and later AI feedback cannot replace teacher assessments. Corrected results inform course recommendations. Tab-scoped journey and quiz draft recovery protects unfinished reasoning, and teachers can search and page through their students. Teachers can replace either reusable class code without changing existing enrollments. Loading and feedback retry behavior preserve the correct results page. A FastAPI backend persists evidence in PostgreSQL; demo activity is separated from clean pilot provisioning.

## Technology

Next.js, React, TypeScript, FastAPI, SQLAlchemy, Alembic, PostgreSQL on Supabase, and Gemini for formative quiz feedback. Authored deterministic rules drive the core diagnostic investigations. Pytest and Playwright verify backend behavior and complete browser workflows.

## Submitted artifacts

- `beyond-marks-demo.mp4`: 109-second narrated and captioned walkthrough of actual app captures.
- `beyond-marks-demo.srt`: companion captions.
- `beyond-marks-demo-transcript.txt`: accessible narration transcript.
- `frontend-pack.pdf`: 18-page captioned screenshot document.
- Repository README: problem/users, four-riddle mapping, setup, architecture and limitations.

## Honest evidence boundary

This is a working prototype with demonstrated persistence and tested workflows. It has not completed a real classroom or month-long retention study. Scheduled dates are not passed checks. AI feedback may be wrong and requires human oversight. Public application hosting is not verified; the repository and downloadable artifacts are the review path.

## Organizer delivery

The supplied slides contain an AIClub@DAU Discord invitation leading to general chat, not an identified submission form. No team name, organizer submission channel/form, or organizer receipt has been provided. Publishing this repository and release is not a claim that the organizers have accepted an entry. Use the exact team identity and submission destination supplied by the participant.
