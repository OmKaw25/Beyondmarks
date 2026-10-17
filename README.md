# Beyond Marks

Beyond Marks helps learners and teachers understand the reasoning behind an answer and decide what to do next. It combines three authored programming investigations with teacher-created subjects, lessons and quizzes. Learners can explain their thinking, question an interpretation, ask for help, and return for genuine delayed checks.

**Intended users:** students learning introductory programming and teachers reviewing a class's reasoning. Teachers may add other subjects and written-answer quizzes; the full authored investigation and practice-variant flow currently covers variables, conditionals and loops.

**Published release:** [video, Frontend Pack and submission ZIP](https://github.com/OmKaw25/Beyondmarks/releases/tag/v1.2.0-hackathon).

**Submission:** [captioned Frontend Pack (PDF)](docs/submission/frontend-pack.pdf) | [HTML gallery](docs/submission/frontend-pack.html) | [project video](docs/submission/beyond-marks-demo.mp4) | [demo script](docs/demo-script.md). Public hosting has not been verified; use the local setup below.

## How the four riddles shaped the product

| Riddle | Design decision | Working behavior |
| --- | --- | --- |
| R1 - Look beyond a mark | Preserve the reasoning that produced the answer. | Learners identify flawed explanation segments, choose an issue and reason, and explain their thinking. Confidence and context self-reports add perspective, including time pressure and incomplete work. |
| R2 - Keep competing explanations open | Show uncertainty and allow the learner to respond. | Authored hypotheses carry supporting and contradicting evidence. Learners can disagree, pause, resume or ask their teacher for help. Earlier interpretations stay in the evidence history. |
| R3 - Ask a useful next question | Prefer a small question that separates plausible explanations. | Distinct output, reading and unhurried probes have different prediction patterns. Selection balances hypothesis separation against interaction burden and exposes its rationale. |
| R4 - Check learning beyond the moment | Separate supported practice, transfer, independence and elapsed-time evidence. | Interactive support leads to changed-context transfer, independent work and reflection. Failed checks adapt support. Completed eligible investigations schedule fresh checks for 7 and 30 days later; server time gates access and submissions are immutable. |

Teachers create subjects and lessons, publish quizzes, and inspect students' answers and reasoning. Gemini supplies formative feedback for class quizzes. Students can dispute it; teachers can append a reasoned correction. Teachers can also assess saved answers immediately when AI feedback is unavailable. Partial assessments count only reviewed questions; later AI results preserve teacher corrections. Original AI output remains available, and the corrected scores update course recommendations. This classroom extension keeps human review in the learning loop.

See the [data model and storage explanation](docs/data-architecture.md) for why enrollment references grow with enrollment count rather than exponentially.

## Architecture and data boundaries

```text
Browser -> Next.js /api proxy -> FastAPI -> PostgreSQL / Supabase
                                  |-- Authored deterministic investigation engines
                                  |-- Gemini written-answer quiz feedback
```

- **Frontend:** Next.js, React and TypeScript; responsive light/dark layouts.
- **Backend:** FastAPI, SQLAlchemy, bcrypt passwords, HttpOnly JWT cookies and revocable database sessions. Learner ownership and teacher assignments scope protected operations.
- **Storage:** additive migrations through `0006`; evidence snapshots, real delayed checks, immutable submissions, append-only reviews and disputes, and materialized course-progress summaries. RLS restricts direct Supabase client access; the trusted backend applies application authorization.
- **Performance:** the teacher roster supports bounded pages, username search and sample-account filtering; classroom queries batch related records; quiz lists, submission lists and teacher evidence timelines are paginated. Recommendations read course summaries rather than rescan full submission history. Expired sessions have an explicit maintenance command.
- **Provenance:** authored content, synthetic demonstration activity and pilot provisioning are separate. `APP_DATABASE_SCHEMA` isolates a named PostgreSQL schema. Accounts default to `data_origin=unverified`; demo and pilot provisioning set explicit origins. An unmarked account is not evidence of a real participant.

Unsubmitted investigation, diagnosis, follow-up, support and verification responses can recover after refresh or a failed request in the same browser tab. Drafts are keyed to the attempt and task, limited to 20 entries and 24 hours, and cleared after successful submission or sign-out. They are not submitted evidence or a server backup; unavailable browser storage does not block learning.

Class-quiz answers and reasoning also recover in the same tab, with a separate limit of 20 drafts and 24 hours. Quiz drafts are keyed by the authenticated learner, quiz and question IDs, preserve the 3,000-character field limit, and are cleared on submission or sign-out. They never store teacher answer keys. If browser storage is unavailable, refresh recovery is unavailable; current-page retry recovery still preserves the form in memory.

No learner-provided code is executed. Programming practice uses authored, validated templates. Correct-answer keys are withheld from unanswered learner tasks. Draft quiz edits are allowed; published questions and submitted answers cannot be silently replaced.

## Local setup - Windows PowerShell

The project has been exercised with Python 3.11 and Node 24. A PostgreSQL connection is required; there is no SQLite or simulated-database fallback.

```powershell
git clone https://github.com/OmKaw25/Beyondmarks.git
cd Beyondmarks
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
Copy-Item .env.example .env
cd frontend
npm.cmd ci
cd ..
```

Keep an existing `.env` rather than overwrite it. Configure secrets locally:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL URI; for Supabase use the **Connect -> Session pooler** URI with an encoded password and TLS settings. |
| `APP_DATABASE_SCHEMA` | Existing application schema, default `public`. Use separate named schemas for pilot and showcase data. |
| `JWT_SECRET` | Random secret of at least 32 characters. |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Class-quiz feedback credentials/model. The configured model is `gemini-3.5-flash-lite`; access and quotas depend on the project. |
| `DEMO_PASSWORD` | Only needed for explicit demo seeding: 10+ characters, at most 72 UTF-8 bytes. |
| `CORS_ORIGINS` | Comma-separated allowed browser origins; local defaults cover port 3000. |
| `SECURE_COOKIES` | `false` for local HTTP, `true` for HTTPS deployment. |
| `TEST_DATABASE_URL` | Optional development PostgreSQL URI with permission to create temporary test schemas. |

Supabase Auth and Supabase browser API keys are not used. Never commit environment files or share the bootstrap credentials file.

### Existing schema or local demonstration

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m app.seed --curriculum-only
# Required on upgrade: populate recommendation summaries from existing graded submissions.
..\.venv\Scripts\python.exe -m app.maintenance rebuild-progress --apply
# Optional, explicit synthetic demonstration users and labelled historical records:
..\.venv\Scripts\python.exe -m app.seed --demo
cd ..
```

`app.seed` now defaults to authored curriculum only. It creates no demo users or learner history unless `--demo` is supplied. Existing records and passwords are retained. Curriculum updates preserve old selected follow-up records while making the current probe version available for new selection.

### Clean pilot or isolated showcase

Bootstrap creates a **new** schema, applies migrations and writes a private, ignored local environment file. It refuses `public`, existing schemas and existing credential files.

```powershell
cd backend
# One pilot teacher, curriculum and class codes; no learner accounts or outcomes.
..\.venv\Scripts\python.exe -m app.bootstrap --schema bm_pilot_2026 --teacher om_teacher --output ../.env.pilot
# Alternative: a separate synthetic showcase with labelled demonstration history.
..\.venv\Scripts\python.exe -m app.bootstrap --schema bm_showcase_2026 --demo --output ../.env.showcase
```

Choose the intended environment file when starting the corresponding backend. Bootstrap files contain database/model configuration, a random JWT secret, teacher credentials and class codes; values are not printed. The following example serves the pilot on port 8001 and uses the generated local port-3001 CORS defaults:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --env-file ../.env.pilot
# In another terminal, from frontend:
$env:API_BASE_URL='http://127.0.0.1:8001'
npm.cmd run dev -- --port 3001
```

For the ordinary root `.env` setup, start two terminals from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-backend.ps1
# Separate terminal:
powershell -ExecutionPolicy Bypass -File scripts/start-frontend.ps1
```

Open **http://127.0.0.1:3000**. API documentation: **http://127.0.0.1:8000/docs**. Database readiness: **http://127.0.0.1:8000/api/ready**. `frontend/.env.local.example` documents `API_BASE_URL`. Restart Next.js after changing its backend configuration.

## Accounts and a complete demonstration

In an explicitly seeded demo, sign in as `teacher_demo` using the local `DEMO_PASSWORD`. **Show class codes** reveals separate student enrollment and teacher referral codes. Student enrollment creates an assignment to that teacher; a referred teacher receives their own class and codes. Codes are not needed at login. `learner_a`, `learner_b` and `learner_c` are synthetic seed accounts.

Teachers can replace either code from **Your class codes** after an inline confirmation. The old code stops accepting future signups; the other code, existing accounts and existing class assignments remain unchanged. The replacement is still reusable. Stale tabs cannot silently replace a code that has already changed; reload the current codes first.

1. Investigate a flawed explanation, then add confidence/context and written reasoning.
2. Inspect competing interpretations and evidence; disagree, pause or request help if appropriate.
3. Answer a diagnostic probe and open **Why this question?**
4. Complete interactive support, transfer, independent work and reflection. Failed checks lead to another example and a fresh check.
5. For an eligible non-demo completed investigation, open **Learning over time** to see persisted 7/30-day due dates. The server rejects early submissions and does not expose early task content. Synthetic demo accounts are excluded from genuine scheduling.
6. In **Subjects & quizzes**, create a subject/course, draft a quiz, edit it, then publish it. Students receive their teacher's published quizzes.
7. Submit answers and reasoning. If AI feedback is unavailable, the original responses remain saved and feedback can be retried.
8. Dispute a quiz result or append a teacher correction. Review history and original AI output remain visible; corrected scores inform recommendations.

Synthetic PASS/FAIL history demonstrates adaptation separately. It must never be presented as observed 7-day or 30-day learning. Browser automation and recorded demonstration accounts are also demonstrations, not research participants.

## Maintenance and verification

```powershell
cd backend
# Preview first; add --apply to remove only expired sessions in the configured schema.
..\.venv\Scripts\python.exe -m app.maintenance cleanup-sessions
# Explicitly classify known automation accounts; repeat --username as needed.
..\.venv\Scripts\python.exe -m app.maintenance mark-demo --username exact_demo_username --apply
..\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
npx.cmd playwright install chromium
# Keep the API running; Playwright starts the frontend.
npm.cmd run test:e2e
```

PostgreSQL tests create isolated random schemas and clean up only their own test data. Browser tests create demonstration accounts and preserve submitted evidence in the configured development schema; use a dedicated showcase/development environment. Avoid running development and production builds against the same `.next` output directory.

Current verification evidence and final release counts belong in [verification results](docs/verification.md). The pilot/performance and existing classroom/learning regression run passed **26 tests**; complete release verification is recorded separately. See [review RCA](docs/review-rca.md), [environment RCA](docs/environment-rca.md) and [retry RCA](docs/retry-rca.md).

## Risks and limitations

- **No longitudinal classroom study has been completed.** Real 7/30-day scheduling, due-time enforcement and immutable observations are implemented; they do not establish learning efficacy or retention. There is no email/push reminder service; learners revisit the scheduled-check screen.
- Hypothesis scores are relative authored evidence weights, not calibrated probabilities, ability rankings or psychological diagnoses. Confidence/context self-report is the learner's perspective, not proof of a cause.
- Programming investigations use structured answer/reasoning checks and retain free text. Gemini evaluates written class-quiz responses; it can be wrong. Teacher review is audited, and feedback needing review is excluded from automatic course scores until resolved.
- Model access, latency, quotas and provider data handling require review before a real school pilot. Quiz question/answer/reasoning text is sent to the configured provider without account identifiers. An outage saves work for retry instead of inventing feedback.
- Independent screens omit hints and answer reveals but cannot prevent outside tools or previously opened tabs. Supervised evaluation is needed to establish independence.
- Fresh practice templates currently cover only the three programming concepts. Their difficulty and educational effectiveness are not calibrated. Teacher-created subjects support lessons/quizzes but do not automatically gain the full investigation or delayed-check content flow.
- The project has scoped authorization and persistence tests, but no production load study or security certification. Recovery workflows, institutional administration and operational monitoring need further work.
- **Public hosting is not verified.** Hosting attempts were blocked in the release environment; no public URL is represented as a working deployment. Local setup and downloadable artifacts are the supported review path.

## Submission materials

- [Frontend Pack PDF](docs/submission/frontend-pack.pdf), [HTML gallery](docs/submission/frontend-pack.html) and [caption/source index](docs/frontend-pack.md)
- [Project video](docs/submission/beyond-marks-demo.mp4), [subtitles](docs/submission/beyond-marks-demo.srt), [transcript](docs/submission/beyond-marks-demo-transcript.txt) and [two-minute narration plan](docs/demo-script.md)
- [Debate and Q&A notes](docs/debate-notes.md)
- [PRD](beyond-marks-prd.md), [TRD](beyond-marks-trd.md), [release plan](docs/superpowers/plans/2026-10-17-hackathon-release.md), [design](design.md), [agent rules](agents.md)

The original PRD/TRD describe the initial baseline. The approved release plan records the later additions: real delayed checks, teacher-created content, AI quiz feedback with review, learner agency and isolated pilot provisioning.
