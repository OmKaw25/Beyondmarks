# Beyond Marks Hackathon Release Plan

> Continuous execution, implementation, verification, commit/push and submission authorized by Om on 2026-10-17 for the next hour. This authorization supersedes earlier phase approval gates and supersedes older PRD non-goals for real retention, teacher-created subjects, AI quiz feedback and release. Use parallel agents for the independent workstreams, with root integrating and verifying.

**Goal:** Finish the approved R1–R4 improvements and produce a verified repository, captioned Frontend Pack and project video within the one-hour release window.

**Architecture:** Extend the existing Next.js/FastAPI/PostgreSQL application. Preserve existing evidence; use additive migrations and audited review records. A real delayed check becomes available based on persisted due dates, never fabricated elapsed time. Teachers review AI feedback and disputes; corrected results inform recommendations. Authored diagnostic probes distinguish plausible causes with minimal burden. New pilot data is separated from demo/test history.

**Deadline:** 2026-10-17 02:32 UTC (08:02 Asia/Kolkata). Target feature integration by 02:02 UTC, verification and artifacts by 02:22 UTC, release by 02:32 UTC.

**Spec:** User's approved improvements in this session, the four original learning riddles, and the fifth submission image. Existing design.md applies.

## Workstreams and interfaces

- [x] Retention/review backend: additive models and migration 0006; schedule real 7/30-day checks after completed learning, due-only access and immutable submissions; fresh questions and failure adaptation; scoped teacher review and student disputes with audit history. Publish API contracts to root for UI wiring. Own models, new retention/review services/routers, migration and focused tests.
- [x] Diagnosis/agency: distinct diagnostic probes, confidence/context self-report (including time pressure/incomplete work), explain uncertainty, pause/resume/help request, richer evidence display. Own catalog/diagnostic journey files and journey UI/types; coordinate hooks with retention backend. Preserve existing tests and answer privacy.
- [x] Data/performance: separate curriculum/bootstrap from demo seeding, clean pilot schema/config without deleting existing data; paginated/batched classroom reads, course progress summaries, expired-session maintenance. Own seed/config/db/classroom services and operational scripts. Coordinate model/migration needs with retention owner.
- [x] Root integration/UI: real check list/answer flow, teacher review/dispute UI, learner/teacher navigation, route registration and additive migration application. Read contracts before integration; avoid shared edits.
- [x] Verify: focused regression tests, full backend suite, typecheck/lint, production build in separate output directory, browser journey and new feature checks, desktop/mobile visual inspection. No fabricated retention outcomes or pilot findings.
- [x] Submission artifacts: README riddle mapping and current limits, captioned PDF/HTML Frontend Pack, <=120-second actual-app video with explanation, release bundle/manifest. Video (109.05 seconds), PDF (16 pages), captions and manifest are complete. Portal/team details were requested asynchronously and remain unavailable.
- [ ] GitHub: scan staged contents for secrets, commit intended files, push to origin, merge/release safely after confirming remote state; publish artifacts and verify links. Submit to provided portal if available and accessible. Report actual acceptance status.

## Boundaries

No destructive resets, no fabricated real student outcomes, no paid infrastructure commitments, no exposing credentials. Authored/generated examples are learning content; demonstration activity is explicitly separated from pilot activity. Public hosting may use available authenticated infrastructure or a clearly labeled temporary tunnel, not an invented deployment. A genuine classroom pilot and month-long outcome cannot be completed in one hour; implement the workflow and measurement capability and report that limitation.

- [ ] Organizer delivery: awaiting exact submission destination and team details; no acceptance receipt claimed.
