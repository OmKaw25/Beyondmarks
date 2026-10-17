# Quiz recovery and invitation controls - 17 October 2026

This section supersedes the historical runs below.

- **Backend:** all 89 tests passed in 581.42 seconds against isolated PostgreSQL schemas. Three existing dependency deprecation warnings remain. The five new invitation tests include simultaneous replacements and signup waiting behind a committed rotation.
- **Browser:** all 25 scenarios passed in one 1.2-minute run. The real frontend/API/Supabase path covers a fresh teacher replacing a student code through the UI, old-code rejection, repeated use of the new code, existing login and existing enrollment. The shared demo teacher's codes were not rotated.
- **Recovery:** real API users/quizzes exercise refresh, 3,000-character reasoning, account/quiz/question isolation, expiry, bounded storage and sign-out. Explicit transport/presentation fixtures exercise request failures, saved-pending responses, blocked storage, teacher retry pagination, invitation conflicts and slow/failed page navigation; these fixtures are not claimed as database persistence evidence.
- **Frontend:** final TypeScript, ESLint and isolated production build passed for all 13 route patterns. Browser tests also verify the corrected page loading behavior.
- **Review:** independent read-only review found the teacher retry pagination defect, now resolved. A separate regression reproduced stale records during page loading. The final blocked-storage recovery regression failed before the page-local memory fallback and passed afterward. No outstanding P1/P2 findings were reported.
- **Data:** no migration, deletion or enrollment reset was needed. Forty-four verified new automation accounts and their activity were classified as demonstrations using exact test naming patterns and known test passwords. No live invitation codes were captured in submission screenshots.
- **Artifacts:** refreshed 18-page Frontend Pack includes an actual quiz form after reload. Desktop/mobile light/dark screenshots are retained; the new PDF page and evidence-boundary page were visually inspected. The existing 109.05-second video still demonstrates the core learning workflow, not every subsequent reliability feature.
- **Limits:** quiz drafts are local to the current tab, with separate 20-entry/24-hour limits. When browser storage is unavailable, only mounted-page retry recovery works; browser refresh cannot restore that memory. Code replacement controls future signup and leaves previously accepted accounts intact.

Public application hosting and organizer acceptance remain unverified. Local setup and published review artifacts remain the handoff.

## Previous verification records

# Classroom reliability verification - 17 October 2026

This section supersedes the historical runs below.

- **Backend:** full local PostgreSQL suite: 84 passed in 406.57 seconds. Three existing dependency deprecation warnings remain. After the final overview pagination refinement, all three focused manual-assessment tests passed in 18.44 seconds, including the previously failing pagination regression. The release CI reruns the full suite against the final source.
- **Browser:** all 18 scenarios passed in one 1.3-minute run. These include actual local frontend/API/Supabase workflows, live Gemini quiz feedback, refresh-safe journey drafts, retry isolation, sign-out cleanup, and searchable teacher rosters. Two new manual-assessment UI scenarios use explicit API fixtures; real PostgreSQL tests separately verify persistence, authorization, partial assessment and a late AI response.
- **Frontend:** TypeScript, ESLint and the isolated production build passed for all 13 route patterns after the final UI changes.
- **Review:** independent review found a quiz-card readiness label issue, fixed with backend projections and browser fixtures. Final inspection also caught a pagination count overwritten by a response count; a failing regression reproduced it before correction. Details are in review-rca.md.
- **Data:** no migration or evidence deletion was needed. Sixteen additional automation accounts were identified by exact test naming patterns and verified test passwords, then marked as demonstration activity along with their attempts and delayed checks. Real classroom outcomes remain unmeasured.
- **Artifacts:** updated 17-page Frontend Pack uses actual application captures, including teacher roster views at 390px/1440px in both themes. Selected PDF pages were visually inspected. The existing 109.05-second narrated/captioned core-workflow video is retained; it does not demonstrate every new reliability feature.
- **Scope:** drafts protect unfinished journey forms within the current tab for up to 24 hours; they are not server backups. Teacher assessment is available during AI outages without treating unanswered assessments as zero. The paged roster endpoint supplements the compatible legacy array endpoint; no production load claim is made.

Public hosting remains unverified. Organizer delivery still needs the exact destination and team identity. Published artifacts and local setup are the supported handoff.

## Previous release verification

# Hackathon release verification - 17 October 2026

This section supersedes the historical runs below.

- **Backend: 79 passed in 420.80 seconds.** Full pytest suite against PostgreSQL using isolated temporary schemas. Three non-failing dependency deprecation warnings: Starlette/httpx and two SQLAlchemy DISTINCT ON warnings.
- **Browser: 12 passed in 42.8 seconds.** Real local frontend, API and configured Supabase database. Includes reusable enrollment codes, role redirects, all learning stages, pause/resume and learner context, fresh retry tasks, teacher-created subjects/quizzes, live Gemini feedback, saved work on request failure, adaptive course ordering, disputes and audited teacher correction.
- **Frontend:** TypeScript and ESLint passed; isolated production build passed for all 13 route patterns. Generated build folders are excluded from lint; source rules are unchanged.
- **Database:** additive migrations through 0006 applied. Four release performance indexes verified in the existing schema; recommendation summaries backfilled. No existing learning evidence was deleted.
- **Pilot provisioning:** separate clean schema created with curriculum and one teacher, no fabricated students or outcomes. Credentials remain in ignored local files. Known browser automation accounts are classified as demonstration activity.
- **Delayed evidence:** tests enforce real due dates, answer privacy, immutable submissions, failure adaptation, assigned-teacher access and provenance after account reclassification. Scheduling is implemented; no real month-long outcome is claimed.
- **Review:** independent read-only review found three P2 gaps; provenance, teacher access to completed delayed explanations and upgrade-summary backfill were resolved. Focused regressions passed before the full suite.
- **Visuals and artifacts:** browser captures cover 390px/1440px and both themes. A 16-page Frontend Pack and 109.05-second narrated/captioned video were generated from actual app captures. Video/audio decode completed successfully; selected frames and PDF pages were visually inspected.
- **Local smoke check:** PostgreSQL readiness returned ready; localhost:3000 returned HTTP 200 after the API restart.
- **Publication checks:** configured secret values and common token patterns were scanned before staging. Environment files, build output and private temporary artifacts are ignored. Release checksums are in the artifact manifest.

GitHub CI passed both backend and frontend jobs for the application release ([run 38993432713](https://github.com/OmKaw25/Beyondmarks/actions/runs/38993432713)). It uses an ephemeral PostgreSQL service, independently of the local Supabase tests. A subsequent packaging follow-up adds explicit route type generation and removes generated declarations from source control; its remote result is recorded in the release handoff.

Public application hosting was not verified. Automatic approval review rejected starting the separate production frontend with only ?blocked by policy?; the unused tunnel was stopped. The working local app, repository and downloadable artifacts are the supported handoff. Organizer submission remains distinct from GitHub publication and requires an identified destination and team details.

## Historical verification records

# Verification — 2026-10-17

Classrooms, enrollment, quizzes, and AI feedback are running locally against the configured Supabase project.

- Backend: 49 tests passed, including real PostgreSQL integration tests in isolated schemas. One existing Starlette/httpx deprecation warning remains.
- Frontend: TypeScript checks and ESLint passed without errors or lint warnings.
- Browser: all 11 scenarios passed across the full run and the focused rerun after correcting an old test's learner selector. Coverage includes teacher/student signup, role redirects, dashboard logo, all seven investigation stages, classroom subjects, draft editing, publication, actual Gemini feedback, recommendation order, failed-submit form preservation, and teacher results.
- Visual: 390px/1440px in light/dark themes; corrected the long-username overflow in teacher results. Screenshots 18–20 show class quizzes, recommendations, and teacher feedback.
- Gemini: live structured grading succeeded using gemini-3.5-flash-lite, including identifying incorrect boundary and loop reasoning. No account identifiers are sent in the grading payload.
- Database: additive migrations through 0005 applied; existing codes, users, passwords, assignments, and submitted evidence retained.

Earlier database test fixture connection interruptions, the model-access restriction, and resolved review findings are recorded in environment-rca.md and review-rca.md. The final backend run passed completely after those interrupted runs.

AI feedback remains formative and can be wrong. Free-tier quotas can delay feedback; submitted answers are saved and retries are available. No live delayed-retention scheduler or public deployment is claimed.

## Fresh programming retries — later verification, 2026-10-17

- Reproduced repeated Learn content and advancing after an incorrect Learn answer with two failing PostgreSQL/API regression tests before implementation. Both passed after the change.
- Full backend suite: 59 passed in 226.47 seconds, with the existing Starlette/httpx deprecation warning. Coverage includes five consecutive failures with fresh content and stable reloads, support/transfer/reflection recovery, stale submissions, and shared variants across students.
- After review moved unnecessary verification-bank reads into the legacy fallback, four focused PostgreSQL/API recovery regressions passed in 34.78 seconds.
- Template answer checks independently execute trusted repository snippets across 20 variants per concept/phase and check answer/rule requirements, hidden answer keys, distinct questions, and varying correct-choice positions. No learner or AI-generated code is executed by the application.
- All 12 browser scenarios passed in one full run, including fresh Learn practice and retrying Transfer before Independent. TypeScript and ESLint passed. Screenshots 21 capture fresh practice at 390px/1440px in light/dark themes; mobile dark and desktop light were visually inspected.
- Read-only independent review found no blocking issues. The unnecessary bank-read finding was addressed. Difficulty equivalence, learning outcomes, and production load remain unvalidated.
- Restarted the local API with reviewed code; `/api/ready` returned ready against PostgreSQL and the frontend returned HTTP 200. No database migration or reset was needed.
