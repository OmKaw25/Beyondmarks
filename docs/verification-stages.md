# Distinct verification stages — requested by Om

Transfer repairs a program in a changed practical context. Independent work requires tracing multiple updates and reporting two results without teaching feedback. Reflect is a slightly harder counterexample or boundary-case challenge; passing independent work alone no longer completes a new journey.

New versioned authored task IDs preserve existing task definitions and submitted evidence. A task's persisted phase and interaction configuration determine its form and grading. Only presentation fields reach the browser; expected answers and scoring keys remain server-side. Reflection uses the existing independent-attempt evidence store with an explicit phase label. Reflection failure recalculates the assessment, changes support, and chooses an unseen reflection challenge.

Already-completed investigations remain complete. Unsubmitted legacy transfer/independent tasks can be advanced to the new bank without rewriting submissions. Difficulty describes the authored progression, not a validated measure of learner ability. Text is retained for teacher review; it is not automatically semantically graded.

Applied migration 0003 and seeded the versioned bank in the configured database. The existing learner's pending Independent task, currently behind an adapted support step, was upgraded after checking it had no submission. The previous and new task IDs are retained in its state for audit.

Verification: 31 non-integration backend tests passed; after a documented database connection interruption, all 12 PostgreSQL integration tests passed, including reflection recovery and stale-submission rejection. Frontend type checking passed. Browser tests completed all seven stages and confirmed the logo returns both roles to their dashboards while retaining authentication.

## Fresh retries — 2026-10-17

Failed Learn predictions now stay in Learn and offer a different short example. Failed Transfer, Independent, and Reflect submissions return to Learn, then retry their original phase with a new question at its original difficulty. Existing submissions and question definitions remain unchanged. A refresh resumes the same persisted question; stale submissions return 409.

Programming templates vary values, boundary cases, and answer/rule positions. Expected results are computed by the template; no learner code or generated AI code runs on the server. Questions are shared by concept/variant and created only when used, while responses remain learner-specific. The existing model and API contract are retained. This applies to variables, conditionals, and loops, not arbitrary teacher-created subjects or published exam questions.

The current checks still evaluate structured reasoning and retain free text for teacher review. Passing a template variant establishes performance on that check, not proven long-term retention. See retry-rca.md for the reproduced causes and verification scope.
