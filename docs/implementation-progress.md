# Current release status

The Supabase-connected application now includes direct teacher assessment during AI outages, partial feedback progress, learner-specific journey/quiz draft recovery, replaceable reusable invitation codes and searchable, paged teacher rosters. Page changes hide stale records and feedback retries preserve the teacher's results page. Core investigations, fresh retries, classrooms, AI feedback with audited review, learner agency, real delayed checks and isolated pilot provisioning remain implemented. See [release verification](verification.md) and [current README](../README.md) for test evidence and limits. The original execution log below is historical.

# Execution ledger — workflow.md

Approved by Om on 2026-10-17. Supabase connection explicitly deferred by Om; implement other work continuously under the earlier request to keep generating the full workflow.

- Workspace: new Git repository on `feat/beyond-marks`; no pre-existing code or branch needed isolation.
- Pre-flight: schema/auth → learner ownership → journey → frontend share UUID identifiers and `{data}` / `{error}` contracts.
- Pre-flight: engine results are authoritative backend output; the frontend never computes a diagnosis.
- Approved resolutions: all rows in workflow.md, including authored priority then ID, meaningful separation, teacher invitations/assignments, revocable cookie sessions, and adaptation to a different support variant.
- Ruling: database integration execution is deferred, as explicitly requested. Keep PostgreSQL-specific schema and real database access; no substitute database. Risk: live migrations and persistence need confirmation after credentials are supplied.
- Verification baseline: Node 24.14.0, npm 11.9.0, Python 3.11.9 through `py -3.11`.
- Phase 1: in progress. Schema tests written before models.
- Phase 1 code prepared: 24 PostgreSQL tables, 32 indexes, frozen SQL migration, Alembic offline output, lazy database configuration. Live migration deferred by user.
- Phases 2–5 code prepared: custom bcrypt/JWT authentication, revocable sessions, learner ownership, teacher assignments, authored curriculum, deterministic engines, all PRD HTTP routes, retained evidence, and synthetic retention adaptation.
- Test-first evidence: schema/engines initially failed on missing modules; auth/API initially failed on missing modules; contract test failed on missing routes. Current suite: 27 passed. PostgreSQL execution still pending.
- RCA: host DEBUG variable collided with boolean settings. Added a failing regression, mapped the setting to BM_DEBUG, and verified the full suite passes. See environment-rca.md.
- Phase 6: frontend implementation in progress; browser acceptance tests written first.
