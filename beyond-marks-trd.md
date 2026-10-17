# Technical Requirements Document (TRD)

## Beyond Marks --- Understanding Learner Reasoning and Enabling Lasting Learning

**Version:** 1.0\
**Status:** Implementation-ready\
**Companion:** `beyond-marks-prd.md`

------------------------------------------------------------------------

## 1. Technical Objective

Build a deterministic, explainable full-stack learning investigation
prototype that implements the complete R1→R4 journey:

**reasoning evidence → competing hypotheses → learner challenge →
informative follow-up → targeted support → transfer → independent
verification → delayed synthetic retention → adaptation**

The system must be understandable and modifiable by a solo developer
using Codex.

------------------------------------------------------------------------

## 2. Architecture

``` text
Next.js Frontend
      |
      | REST/JSON + JWT
      v
FastAPI Backend
      |
      +--> Rule / Diagnostic Engine
      |
      +--> Auth / Authorization
      |
      +--> PostgreSQL via Supabase
```

Recommended repository:

``` text
/
├── frontend/
├── backend/
├── database/
├── docs/
├── scripts/
├── tests/
├── README.md
├── AGENTS.md
└── .env.example
```

------------------------------------------------------------------------

## 3. Stack

### Frontend

-   Next.js
-   React
-   TypeScript
-   CSS modules or a lightweight utility approach
-   No unnecessary component framework dependency

### Backend

-   Python
-   FastAPI
-   Pydantic
-   SQLAlchemy or SQLModel
-   bcrypt
-   JWT implementation

### Database

-   Supabase PostgreSQL

### Hosting

-   Vercel for frontend where practical.
-   Backend deployment must use a free compatible platform if used.
-   Local execution is mandatory and authoritative.
-   Do not require paid services.

------------------------------------------------------------------------

## 4. Configuration

Frontend environment:

``` text
NEXT_PUBLIC_API_BASE_URL=
```

Backend:

``` text
DATABASE_URL=
JWT_SECRET=
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=
```

Never commit actual secrets.

Provide `.env.example`.

------------------------------------------------------------------------

## 5. Backend Structure

Recommended:

``` text
backend/app/
├── main.py
├── config.py
├── db.py
├── models/
├── schemas/
├── routers/
│   ├── auth.py
│   ├── learner.py
│   ├── investigations.py
│   ├── retention.py
│   └── teacher.py
├── services/
│   ├── auth_service.py
│   ├── diagnostic_engine.py
│   ├── followup_engine.py
│   ├── support_engine.py
│   ├── adaptation_engine.py
│   └── seed_service.py
├── security/
│   ├── hashing.py
│   ├── jwt.py
│   └── dependencies.py
└── tests/
```

Keep route handlers thin. Put business logic in services.

------------------------------------------------------------------------

## 6. Diagnostic Engine

Input: - exercise; - learner correction; - selected broad category; -
selected specific reason; - optional explanation; - previous evidence; -
previous challenge; - follow-up answers.

Output:

``` json
{
  "hypotheses": [
    {
      "id": "loop_iteration",
      "score": 0.68,
      "confidence": "Medium",
      "supporting_evidence": [],
      "contradicting_evidence": []
    }
  ],
  "uncertain": false
}
```

### Scoring

For each active hypothesis:

``` text
raw =
  prior_weight
  + sum(supporting evidence weights)
  - sum(contradicting evidence weights)
  - unresolved_penalty
```

Normalize with:

``` text
normalized_i = max(raw_i, 0) / sum(max(raw_j, 0))
```

If all raw values are zero, assign equal probability.

Confidence:

``` text
High >= 0.75
Medium 0.50–0.74
Low < 0.50
```

Uncertain:

``` text
top_score - second_score < 0.15
```

Treat uncertainty as a first-class state.

------------------------------------------------------------------------

## 7. Evidence Extraction

Do not use NLP/LLM to infer arbitrary meaning.

Evidence comes from deterministic UI actions: - selected segment; -
selected broad category; - selected specific reason; - selected
answer; - correctness; - predefined explanation tags; - learner
challenge; - follow-up answer; - support prediction; - transfer
result; - independent result.

Optional free text is stored for teacher context but is not required for
core scoring.

------------------------------------------------------------------------

## 8. Learner Challenge

Endpoint receives:

``` json
{
  "alternative_hypothesis_id": "condition_logic",
  "reason": "The condition is evaluated before the loop body."
}
```

Rules: - alternative must belong to the current exercise; - system
interpretation is retained; - learner disagreement is stored; - teacher
view displays it; - challenge must not mutate historical evidence.

------------------------------------------------------------------------

## 9. Follow-up Engine

For each active follow-up:

``` text
predictions = predictions for active hypotheses
distinct = unique(predictions)
divergence = len(distinct) / len(active_hypotheses)
final_score = divergence * 100 - burden_score
```

Reject: - inactive follow-ups; - follow-ups already answered; -
follow-ups that do not target the active hypotheses.

Tie-break: 1. divergence; 2. lower burden; 3. lower estimated effort; 4.
deterministic ID order.

Persist: - selected follow-up; - divergence; - burden; - final score; -
rationale; - timestamp.

Rationale example:

> "The two leading explanations predict different outcomes for this
> question, so your answer will help distinguish them."

------------------------------------------------------------------------

## 10. Support Engine

Support modules are authored in the database.

Each contains: - explanation; - worked example; - prediction prompt; -
answer choices; - correct choice; - feedback.

The system selects the module associated with the current leading
hypothesis or updated hypothesis after adaptation.

Completion is recorded only after the prediction interaction is
submitted.

------------------------------------------------------------------------

## 11. Transfer Engine

Transfer task must: - reference the same concept; - use different
wording; - use different variable names; - use changed surrounding
context; - use new code; - have deterministic expected output.

A transfer attempt stores: - answer; - explanation; - correctness; -
evidence tags; - timestamp.

------------------------------------------------------------------------

## 12. Independent Engine

Independent task: - new prompt; - new code; - no hints; - no support; -
no answer reveal; - requires answer + explanation.

Scoring must remain evidence-oriented.

Suggested fields:

``` text
correct
explanation_present
explanation_evidence_tags
```

A correct answer with weak explanation must not automatically be treated
as equivalent to demonstrated understanding.

------------------------------------------------------------------------

## 13. Retention Engine

Retention records are explicitly seeded.

Schema requirements:

``` text
is_synthetic = true
check_date = approximately current_date - 30 days
```

Demo dataset must contain: - PASS record; - FAIL record.

UI label: **Synthetic demo record --- not a real longitudinal
observation**

Never generate a fake claim that the learner actually participated one
month earlier.

------------------------------------------------------------------------

## 14. Adaptation Engine

Trigger: - independent failure or delayed synthetic failure.

Algorithm: 1. Load previous hypothesis assessment. 2. Add new failure
evidence. 3. Recalculate hypotheses. 4. Compare old vs new leading
hypothesis. 5. Select support for the new leading hypothesis. 6. Create
adaptation event. 7. Generate/select a new verification task.

Persist old and new assessments for auditability.

The system should be able to say:

> "The previous explanation was not sufficiently supported by later
> evidence. We changed the interpretation and selected different
> support."

------------------------------------------------------------------------

## 15. API Standards

All API responses use JSON.

Success:

``` json
{
  "data": {}
}
```

Error:

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Readable error",
    "details": {}
  }
}
```

HTTP guidance: - 200 successful read/update; - 201 creation; - 400
invalid request; - 401 unauthenticated; - 403 unauthorized; - 404
missing resource; - 409 duplicate/conflict; - 422 schema validation; -
500 unexpected server error.

------------------------------------------------------------------------

## 16. Authentication

Signup: 1. Validate username/password. 2. Hash password using bcrypt. 3.
Create user. 4. Return authenticated session/JWT or require login.

Login: 1. Fetch by username. 2. Verify bcrypt hash. 3. Issue JWT. 4. Do
not return password hash.

JWT claims:

``` json
{
  "sub": "<user_id>",
  "role": "learner",
  "exp": 0
}
```

Server must derive authorization from verified token/user record.

------------------------------------------------------------------------

## 17. Authorization

Implement dependencies: - `get_current_user()` - `require_learner()` -
`require_teacher()`

Learner queries must filter by authenticated learner ID.

Teacher endpoints must verify teacher role before querying learner
evidence.

Never accept arbitrary `learner_id` from the browser as sufficient
authorization.

------------------------------------------------------------------------

## 18. Database Implementation

Use migrations.

Recommended migration sequence: 1. users/profiles; 2.
concepts/exercises; 3. explanation segments; 4. hypotheses/rules; 5.
follow-ups/predictions; 6. attempts/evidence; 7. challenges/assessments;
8. support; 9. transfer/independent; 10. retention/adaptation.

Add foreign keys and useful indexes.

Recommended indexes: - users(username); - attempts(learner_id,
created_at); - learner_evidence(attempt_id); -
hypothesis_assessments(attempt_id); -
hypothesis_assessments(hypothesis_id); -
learner_challenges(attempt_id); - follow_up_selections(attempt_id); -
retention_checks(learner_id, check_date).

------------------------------------------------------------------------

## 19. Seed System

Create an idempotent seed command.

Example:

``` bash
python -m app.seed
```

Seed: - concepts; - exercises; - explanation segments; - hypotheses; -
evidence rules; - follow-ups; - predictions; - support modules; -
transfer tasks; - independent tasks; - synthetic retention records; -
demo users.

Seed command must not duplicate records on repeated execution.

------------------------------------------------------------------------

## 20. Frontend Architecture

Recommended:

``` text
frontend/
├── app/
│   ├── page.tsx
│   ├── login/
│   ├── signup/
│   ├── learner/
│   ├── investigate/[id]/
│   ├── diagnosis/[id]/
│   ├── follow-up/[id]/
│   ├── support/[id]/
│   ├── transfer/[id]/
│   ├── independent/[id]/
│   ├── retention/[id]/
│   └── teacher/
├── components/
│   ├── CodeBlock
│   ├── EvidenceCard
│   ├── HypothesisCard
│   ├── ConfidenceBadge
│   ├── WhyThisQuestion
│   ├── ProgressStepper
│   └── SyntheticDataBadge
├── lib/
│   ├── api.ts
│   ├── auth.ts
│   └── types.ts
└── styles/
```

Prefer reusable components over duplicated page logic.

------------------------------------------------------------------------

## 21. Frontend State

Each stage should have: - idle; - loading; - submitting; - success; -
validation error; - server error.

Prevent duplicate submissions.

After successful mutation, either: - update local state from response; -
or refetch authoritative state.

Do not optimistically display a diagnosis that the backend did not
calculate.

------------------------------------------------------------------------

## 22. UX Requirements

The investigation page should make the evidence relationship visually
obvious:

``` text
Question
   ↓
Code / Expected Result
   ↓
Flawed Explanation
   ↓
What is wrong?
   ↓
Broad Category
   ↓
Specific Reason
   ↓
Why?
```

Diagnosis page:

``` text
Leading explanation
Confidence
Evidence

Alternative explanation
Confidence
Evidence

[Agree] [I disagree]
```

Follow-up page:

``` text
Why this question?
------------------
Hypothesis A predicts: X
Hypothesis B predicts: Y

Selected question
[Answer]
```

This structure should make the product thesis understandable even
without narration.

------------------------------------------------------------------------

## 23. Design Tokens

Define:

``` css
--bg;
--surface;
--surface-muted;
--text;
--text-muted;
--primary;
--primary-hover;
--accent;
--border;
--success;
--warning;
--danger;
--radius-sm;
--radius-md;
--radius-lg;
--shadow-sm;
--shadow-md;
```

Use tokens throughout.

Dark mode must replace tokens, not duplicate entire components.

------------------------------------------------------------------------

## 24. Accessibility

Minimum: - semantic headings; - form labels; - keyboard navigation; -
visible focus; - buttons with clear labels; - errors associated with
inputs; - no color-only status communication; - readable code blocks; -
responsive layout.

------------------------------------------------------------------------

## 25. Observability / Debugging

Development logs should include: - request ID; - route; - user ID where
safe; - stage; - rule-engine decision; - selected follow-up; -
adaptation event.

Do not log: - passwords; - JWT secrets; - sensitive authentication
tokens.

Create a debug mode that can show rule-engine calculations in
development only.

------------------------------------------------------------------------

## 26. Tests

### Diagnostic engine

Test: - single clear hypothesis; - two competing hypotheses; - equal
hypotheses; - contradiction; - uncertainty threshold; - challenge
evidence.

### Follow-up

Test: - maximum divergence wins; - burden breaks ties; - already
answered question rejected; - no meaningful separation handled.

### Adaptation

Test: - failure causes recalculation; - support changes when leading
hypothesis changes; - adaptation event persists old/new state.

### Security

Test: - incorrect password; - duplicate username; - missing JWT; -
learner accessing another learner; - learner calling teacher endpoint.

### End-to-end

Run the full R1→R4 path with seeded data.

------------------------------------------------------------------------

## 27. Performance / Reliability

This is a hackathon prototype, but avoid obviously wasteful behavior.

Requirements: - no unnecessary polling; - database queries should be
scoped and indexed; - diagnosis calculation should be synchronous and
deterministic; - pages should not block on unrelated data; - errors
should be recoverable.

No external AI API call is required.

------------------------------------------------------------------------

## 28. Deployment

### Local

Backend:

``` bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

``` bash
cd frontend
npm install
npm run dev
```

### Database

Configure Supabase connection string.

Run migrations and seed.

### Production

Frontend can deploy to Vercel.

Backend deployment is optional for the local-first demo but should be
documented if selected. Ensure FastAPI deployment platform is compatible
with the application's runtime and free-tier constraints.

------------------------------------------------------------------------

## 29. Definition of Done

Technical implementation is done when: - migrations run from a clean
database; - seed is idempotent; - backend starts; - frontend starts; -
signup/login works; - role authorization works; - full learner flow
works; - teacher evidence view works; - synthetic data is visibly
labelled; - diagnostic and follow-up calculations are deterministic; -
adaptation is demonstrated; - automated tests pass; - no secrets are
committed; - README explains setup and architecture.

------------------------------------------------------------------------

## 30. Implementation Priority

If implementation order is required, use:

**P0** 1. database + migrations; 2. auth; 3. exercise/diagnostic data;
4. investigation; 5. hypothesis engine; 6. challenge; 7. follow-up
engine; 8. support; 9. transfer; 10. independent; 11.
retention/adaptation.

**P1** 12. teacher dashboard; 13. polished states; 14. theme system; 15.
accessibility refinement; 16. tests and demo tooling.

Do not remove R1→R4 functionality to make room for cosmetic polish.

------------------------------------------------------------------------

## 31. Codex Engineering Rules

1.  Read `AGENTS.md` before modifying code.
2.  Preserve the PRD's locked decisions.
3.  Do not introduce an LLM unless explicitly approved.
4.  Do not replace deterministic business rules with opaque heuristics.
5.  Keep business logic out of React components and route handlers.
6.  Validate at API boundaries.
7.  Write tests for every rule-engine change.
8.  Never store plaintext passwords.
9.  Never commit secrets.
10. Do not label synthetic retention records as real.
11. Keep learner evidence immutable after submission; append new
    evidence instead.
12. Prefer small, testable functions.
13. Use typed API contracts.
14. Do not create leaderboard functionality.
15. When uncertain, preserve transparency and explicitly expose
    uncertainty rather than inventing confidence.
