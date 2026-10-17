# Beyond Marks Implementation Plan

> Historical baseline plan. Implementation and later scope are recorded in [the release plan](docs/superpowers/plans/2026-10-17-hackathon-release.md), [current README](README.md), and [verification evidence](docs/verification.md). Supabase is now connected. Later user instructions authorize AI quiz feedback, reusable teacher/student codes, real delayed checks, continuous execution and GitHub publication; these supersede the older restrictions and pending prerequisites below. Original planning checkboxes are retained as historical records rather than retrospective test claims.

> **Status: Approved by Om on 2026-10-17.** The PRD and TRD are the supplied product specification. This plan fills implementation gaps without changing those source documents. Supabase connection and live database verification are explicitly deferred by Om; continue implementing other work.
>
> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task by task in this session. Steps use checkbox syntax. Follow `agents.md`; report each completed phase and obtain the required confirmation unless Om explicitly authorizes continuous execution.

**Goal:** Deliver a locally runnable, persistent frontend-to-backend Beyond Marks application implementing the full R1–R4 journey for variables, conditionals, and loops.

**Architecture:** A Next.js App Router frontend calls a FastAPI REST API. FastAPI owns authentication, authorization, stage transitions, evidence evaluation, and deterministic learning engines. Supabase PostgreSQL persists authored content, immutable learner evidence, assessment snapshots, and adaptation history.

**Tech Stack:** Next.js, React, TypeScript, CSS modules and shared CSS tokens; Python, FastAPI, Pydantic, SQLAlchemy, Alembic, bcrypt, PyJWT, psycopg; Supabase PostgreSQL. Proposed verification tools: pytest, HTTPX, and Playwright.

**Spec:** `beyond-marks-prd.md`, `beyond-marks-trd.md`, `agents.md`; proposed visual specification: `design.md`.

## Global constraints

- No LLM, NLP diagnosis, paid services, or arbitrary code execution.
- Core concepts: variables/state, conditionals, and loops.
- Custom FastAPI signup/login; bcrypt password hashing; JWT sessions.
- Supabase PostgreSQL is the application database. No silent SQLite, in-memory, or mocked database fallback.
- Preserve submitted learner evidence; append new evidence and assessments.
- Free text is retained for teacher context. Structured choices and authored tags drive scoring.
- Every delayed seed record is visibly labelled: **Synthetic demo record — not a real longitudinal observation**.
- An unseen independent check has no hints, support, or answer reveal and requires a solution and explanation.
- No class leaderboard and no claim that synthetic records prove retention.
- Complete the R1–R4 journey before cosmetic expansion.
- Local execution is mandatory; publishing is outside this implementation plan.

## Decisions proposed for review

These proposals address incomplete or conflicting details. They are not approved changes to the PRD or TRD.

| Topic | Proposed resolution | Reason |
| --- | --- | --- |
| Follow-up tie-break conflict | Highest selection score, then higher divergence, lower burden, lower estimated effort, authored priority, stable ID. | PRD ends with authored priority; TRD ends with ID. Include both in a defined order. |
| Meaningful separation | Preserve the supplied divergence formula, but treat fewer than two active hypotheses or fewer than two distinct predicted answers as providing no separation. Reject incomplete prediction maps. | A nonzero arithmetic score alone does not establish useful separation. |
| Inconclusive cases | Record the inconclusive decision, show why, and offer an authored general concept lesson with the lowest burden. Do not label it targeted diagnosis. | Implements the PRD fallback without inventing a confident explanation. |
| Confidence normalization | Clamp raw scores at zero; use an equal distribution if their sum is zero. Compute uncertainty from unrounded values. | Covers negative as well as zero raw scores and prevents division by zero. |
| Teacher permissions | Learner signup is public. Teacher signup requires an environment-configured invitation code. Teachers can read only explicitly assigned learners. Seed teacher assignments for the demo. | PRD permits role selection but requires server-controlled roles and permitted learner access. Public role choice alone cannot grant teacher privileges. |
| JWT transport and logout | Use a Next.js same-origin API proxy to FastAPI. Set an HttpOnly session cookie; use Secure in production and SameSite protection. Persist revocable sessions so logout invalidates the JWT session. | Supports protected pages and meaningful logout without storing tokens in browser localStorage. |
| Investigation identity | An investigation URL ID represents a learner-owned attempt. Starting an exercise creates an attempt via an additional POST endpoint. | Separates reusable authored content from a learner's immutable submissions and enables resume. |
| Explanation evaluation | Require explanation text and authored reasoning choices/tags in independent checks. Validate tags against the task. Store text without automatic semantic grading. | Reconciles explanation evaluation with the explicit prohibition on NLP/LLM inference. |
| Failure adaptation | Keep old assessments; add failure evidence; recalculate. Choose a different authored support variant even if the leading hypothesis remains unchanged. Select an unseen verification task. | The PRD requires changed support, while TRD describes changing the leading hypothesis only when evidence warrants it. |
| Attempt completion | Transfer records evidence; independent failure enters adaptation. Successful independent completion proceeds to retention review. Synthetic retention adaptation creates a separately labelled demonstration run. | Prevents synthetic history from being confused with live learner performance. |
| Synthetic history | Seed dated PASS/FAIL records and a complete synthetic baseline needed to demonstrate adaptation. Use Asia/Kolkata calendar dates for demo timestamps. | Prevents implying a newly registered user actually participated a month earlier. |
| Validation | Usernames: 3–32 characters, letters/digits/underscore; case-insensitive uniqueness. Passwords: at least 10 characters and at most 72 UTF-8 bytes. Explain errors before submission. | Supplies missing validation values and respects bcrypt's byte limit. |

## Review focus

1. A learner changes an attempt ID or request body to access another learner: every query checks authenticated ownership.
2. A browser retries, refreshes, or submits twice: preserve immutable evidence and return the established result or a clear conflict, never duplicate evidence.
3. Hypotheses tie, all scores are nonpositive, or predictions agree: show uncertainty and an appropriate inconclusive path.
4. An independent task is opened: its API payload excludes correct answers, feedback keys, and scoring rules, including before submission.
5. Later evidence fails to confirm learning: preserve the original assessment, change the support, and ensure the verification task is genuinely new.

## File and responsibility map

| Location | Responsibility |
| --- | --- |
| `backend/app/config.py`, `db.py` | Validated environment configuration and PostgreSQL session management. |
| `backend/app/models/` | SQLAlchemy schema, constraints, relationships, and indexes. |
| `backend/alembic/` | Versioned migrations, including content and auth tables. |
| `backend/app/schemas/` | Request validation and explicit public response schemas. |
| `backend/app/security/` | Password hashing, JWTs, session revocation, and role/ownership dependencies. |
| `backend/app/services/diagnostic_engine.py` | Pure deterministic evidence scoring and uncertainty. |
| `backend/app/services/followup_engine.py` | Pure selection, divergence, burden, and rationale. |
| `backend/app/services/journey_service.py` | Attempt ownership, legal transitions, transactions, and resume state. |
| `backend/app/services/support_engine.py` | Authored support selection and completion. |
| `backend/app/services/assessment_service.py` | Transfer and independent result/tag evaluation. |
| `backend/app/services/adaptation_engine.py` | New evidence, revised interpretation, different support, and unseen verification. |
| `backend/app/routers/` | Thin auth, learner, investigation, retention, and teacher HTTP handlers. |
| `backend/app/content/`, `backend/app/seed.py` | Authored exercises and idempotent synthetic demo seed. |
| `backend/tests/` | Engine, API, security, migration, and seed tests. |
| `frontend/app/` | Required page routes and same-origin API proxy. |
| `frontend/components/` | Shared accessible forms, navigation, evidence, hypotheses, and synthetic labels. |
| `frontend/lib/` | Typed API contracts, errors, and session helpers. |
| `frontend/styles/` | Shared tokens from `design.md`, global styles, and responsive behavior. |
| `tests/e2e/` | Browser verification against the actual FastAPI application and PostgreSQL. |
| `scripts/` | Local startup and verification scripts for Windows. |
| `README.md`, `.env.example`, `docs/` | Setup, architecture, limitations, demo instructions, and documented RCA if needed. |

## Phase 1 — Database, configuration, and migrations

**Deliverable:** FastAPI health endpoint and a real migrated Supabase PostgreSQL database.

**Interfaces:** `get_settings() -> Settings`; `get_db() -> Iterator[Session]`; success `{data: ...}` and errors `{error: {code, message, details}}`.

- [ ] Configure repository ignores, backend environment, dependency manifests, and `.env.example`. Generate secrets locally; never log them.
- [ ] Add migration/schema tests asserting required tables, foreign keys, unique usernames, and lookup indexes.
- [ ] Run the tests before implementation and confirm they fail for missing schema.
- [ ] Implement models for all PRD tables, plus proposed sessions and teacher assignments; apply Alembic migrations to a configured development database.
- [ ] Implement health/readiness and uniform validation/error responses; database failure must remain explicit.
- [ ] Run `python -m pytest tests/test_schema.py -q` and `python -m alembic upgrade head` from `backend`; verify readiness against PostgreSQL.
- [ ] Report completed work, test results, and any remaining configuration requirement.

## Phase 2 — Authentication and authorization

**Deliverable:** Signup/login/me/logout with role, ownership, and teacher-assignment enforcement.

**Interfaces:** `get_current_user() -> User`; `require_learner() -> User`; `require_teacher() -> User`; auth routes as defined in PRD section 17. Proposed teacher invitation validated server-side.

- [ ] Write API tests for valid signup/login, invalid credentials, duplicate username, expired/revoked JWT, unauthorized teacher enrollment, and forbidden learner access.
- [ ] Confirm failure, then implement bcrypt, JWT sessions, account status checks, and assignment checks.
- [ ] Test 72-byte password boundaries, including multibyte characters; ensure hashes and tokens never appear in public errors.
- [ ] Run `python -m pytest tests/test_auth.py tests/test_permissions.py -q` against PostgreSQL.
- [ ] Report the working authenticated API and the next phase.

## Phase 3 — Authored content, investigation, and hypotheses

**Deliverable:** Learners start/resume investigations, submit immutable structured reasoning, view hypotheses, and disagree.

**Interfaces:** `assess(hypotheses, evidence) -> AssessmentResult`; `start_attempt(session, learner, exercise_id) -> Attempt`; `submit_correction(session, learner, attempt_id, correction) -> AssessmentResult`.

- [ ] Write engine tests for supporting/contradicting evidence, unequal priors, zero/nonpositive totals, close scores, exact confidence boundaries, and disagreement evidence.
- [ ] Write API tests for invalid segment/category/reason combinations, foreign hypotheses, repeated submissions, ownership, and legal stage transitions.
- [ ] Implement authored variables, conditionals, and loops exercises, including realistic alternative explanations and structured reasoning tags.
- [ ] Implement evidence rules, assessments, challenge history, and explicit uncertain states; preserve original assessments when a learner disagrees.
- [ ] Seed demo learners illustrating correct-but-lucky, clear misconception, partial understanding, and disagreement cases. Add teacher assignments.
- [ ] Verify seed idempotency by running twice and asserting unchanged record counts and relationships.
- [ ] Run `python -m pytest tests/test_diagnosis.py tests/test_investigations.py tests/test_seed.py -q`.
- [ ] Report the persisted investigation-to-diagnosis path.

## Phase 4 — Informative follow-up and targeted support

**Deliverable:** One selected follow-up, a meaningful rationale, updated evidence, and an interactive support lesson.

**Interfaces:** `select_followup(candidates, active_hypotheses, answered_ids) -> SelectionResult`; `choose_support(assessment, content, excluded_ids) -> SupportChoice`.

- [ ] Write tests for maximum selection score, each approved tie-break, inactive/already-answered candidates, incomplete predictions, no separation, and no candidates.
- [ ] Implement the supplied divergence and burden formulas with approved meaningful-separation behavior.
- [ ] Persist the chosen question, predictions, rationale, burden, and score. Do not expose correct-answer keys.
- [ ] Record the answer as new evidence and recalculate assessment. Preserve the selection snapshot explaining why the question was originally chosen.
- [ ] Implement authored mini-lessons with worked examples, predictions, and feedback. Completion requires a submitted prediction.
- [ ] Run `python -m pytest tests/test_followup.py tests/test_support.py -q`.
- [ ] Report the functioning investigation → diagnosis → follow-up → support path.

## Phase 5 — Transfer, independence, retention, and adaptation

**Deliverable:** Complete R1–R4 backend journey with real persisted live work and separately labelled synthetic history.

**Interfaces:** `evaluate_task(task, response) -> TaskResult`; `adapt(session, learner, source_check) -> AdaptationResult`; return the next stage/task without rewriting evidence.

- [ ] Write tests for changed-context tasks, answer-plus-reasoning evaluation, no answer leakage, stage enforcement, and replayed mutation requests.
- [ ] Implement transfer and independent endpoints with explicit safe response schemas and authored reasoning tags.
- [ ] Seed PASS/FAIL historical checks with `is_synthetic=true` and link them to synthetic baseline evidence.
- [ ] Write adaptation tests: old assessment preserved, new failure evidence appended, changed support, unseen task, and clear synthetic provenance.
- [ ] Implement adaptation for independent and delayed failures, including support changes when the leading hypothesis remains unchanged.
- [ ] Run `python -m pytest tests/test_assessment.py tests/test_retention.py tests/test_adaptation.py tests/test_journey.py -q`.
- [ ] Report the full backend journey and its verification status.

## Phase 6 — Connected frontend and teacher evidence view

**Deliverable:** All PRD routes connected to the real backend with a consistent approved design.

**Interfaces:** A typed `api<T>(path, options) -> Promise<T>` unwraps `{data}` and produces structured API errors. Frontend state follows server-returned attempt stage and next action.

- [ ] Implement Next.js, approved design tokens, light/dark mode, same-origin proxy, and authentication pages.
- [ ] Implement landing, learner home, investigation, diagnosis/challenge, follow-up, support, transfer, independent, and retention/adaptation pages.
- [ ] Implement teacher routes and API evidence timeline restricted to permitted learners. Include learner disagreement, selection rationale, and old/new adaptation assessments.
- [ ] Provide loading, empty, error/retry, validation, submitting, and success states. Disable duplicate submission; restore progress after refresh.
- [ ] Keep support links and answer assistance out of the independent task. Explain the limit: external tools cannot be technically prevented by this app.
- [ ] Add browser tests for signup/login, both learner agreement and disagreement, follow-up rationale, support prediction, transfer, independent outcome, retention, adaptation, and teacher review.
- [ ] Run `npm run typecheck`, `npm run lint`, `npm run build` from `frontend`, and the browser suite against the running API/PostgreSQL.
- [ ] Report a runnable frontend/backend pair and browser evidence, including any failing path.

## Phase 7 — Full verification and handoff

**Deliverable:** A documented local application with reproducible setup and an honest demonstration of all four riddles.

- [ ] Run the complete backend test suite against a separate PostgreSQL test database/schema; never reset a user or production database.
- [ ] Exercise clean migrations and repeatable seeding. Verify live records and synthetic records remain distinguishable.
- [ ] Run browser flows at desktop and mobile widths, in both themes. Check keyboard navigation, error recovery, refresh/resume, and role separation.
- [ ] Run frontend production build and local smoke tests. Inspect logged output for accidental credentials or raw database errors.
- [ ] Write README setup/run instructions, architecture, riddle mapping, limitations, and Frontend Pack reference; add caption list, two-minute demo script, and debate notes.
- [ ] Document remaining external prerequisites precisely. Do not claim Supabase connectivity or month-long retention without real evidence.
- [ ] Present the local URLs, test results, and any material limitations.

## Current prerequisites

- Python 3.11 is available through `py -3.11`. Create the backend virtual environment with `py -3.11 -m venv .venv`; run documented Python commands inside that environment. The bare system `python` command currently points to a nonfunctional Store alias.
- Om's review of the proposed gap resolutions and `design.md` values.
- An isolated development Supabase PostgreSQL connection configured locally. No connection string is currently present in the workspace or environment.
- A separate test database/schema that may be migrated and reset during automated tests.
- Decision on continuous execution versus the existing phase confirmation rule in `agents.md`.

No product code, migrations, dependencies, external services, or credentials have been created as part of this planning document.
