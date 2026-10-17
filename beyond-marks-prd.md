# Product Requirements Document (PRD)

## Beyond Marks --- Understanding Learner Reasoning and Enabling Lasting Learning

**Version:** 1.0\
**Status:** Implementation-ready\
**Audience:** Codex / engineering agent, frontend/backend implementers,
hackathon judges\
**Primary user:** Learner\
**Secondary user:** Teacher/Mentor\
**Subject:** Basic programming --- variables, conditionals, loops\
**AI approach:** Deterministic rules only; no LLM required\
**Data policy:** Demo/seeded delayed-retention records are synthetic and
must be visibly labelled.

------------------------------------------------------------------------

## 1. Product Summary

Beyond Marks is a learner-centered investigation system that goes beyond
a score. It captures evidence of how a learner reasons, maintains
competing explanations for observed difficulty, asks the single most
informative next question, provides targeted support, and verifies
whether understanding transfers and persists.

The complete journey is:

**Question → flawed explanation investigation → evidence → competing
hypotheses → learner challenge → informative follow-up → targeted
support → transfer → independent no-tool check → delayed retention →
adaptation if needed**

The product must never present a diagnosis as unquestionable fact. It
must expose uncertainty and allow the learner to disagree.

------------------------------------------------------------------------

## 2. Problem

Marks, grades, completion, streaks and rankings hide the reasoning
behind an answer. Two learners with the same score may need very
different support. The same wrong answer can result from a
misconception, missed condition, execution-order confusion, time
pressure, or another cause.

The product therefore needs to: 1. Reveal understanding beyond the
result. 2. Distinguish plausible causes before prescribing support. 3.
Choose one informative next interaction while minimizing burden. 4. Make
learner, educator and system roles explicit. 5. Verify transfer,
independence and retention. 6. Adapt interpretation and support when
later evidence contradicts the earlier conclusion.

------------------------------------------------------------------------

## 3. Goals

### Primary goals

-   Capture reasoning evidence, not just correctness.
-   Produce multiple plausible, evidence-ranked explanations.
-   Show confidence/uncertainty transparently.
-   Let learners challenge the system's interpretation.
-   Select the follow-up with maximum predicted answer separation.
-   Explain why the follow-up was selected.
-   Provide targeted interactive support.
-   Test transfer using changed context and new code.
-   Test independent understanding with a new problem, no hints/tools,
    plus a short explanation.
-   Demonstrate delayed retention with clearly labelled synthetic
    historical checks.
-   Demonstrate failure → re-diagnose → changed support → re-test.
-   Give teachers evidence, uncertainty and learner disputes without
    leaderboard-style ranking.

### Non-goals

-   General-purpose tutoring for arbitrary subjects.
-   LLM-generated tutoring or diagnosis.
-   Automated high-stakes grading.
-   Real claims about one-month retention from seeded data.
-   Competitive class rankings.
-   Email verification, password reset, SMS, paid APIs or paid
    infrastructure.

------------------------------------------------------------------------

## 4. Locked Product Decisions

  -----------------------------------------------------------------------
  Area                                Decision
  ----------------------------------- -----------------------------------
  Learner correction                  Structured correction

  Context                             Question + relevant code + expected
                                      output/result + flawed explanation

  Diagnosis                           Two-level broad category + specific
                                      reason

  Challenge                           Learner can disagree and choose an
                                      alternative interpretation

  Hypotheses                          Hybrid: authored hypothesis pool +
                                      deterministic evidence rules

  Follow-up selection                 Maximum separation

  Support                             Interactive mini-lesson

  Transfer                            Changed context + new code

  Independent check                   New problem + no hints/tools +
                                      explain and solve

  Failure adaptation                  Re-diagnose + change support +
                                      re-test

  Retention                           Two seeded historical checks: one
                                      pass, one fail

  AI                                  No LLM; deterministic rules

  Auth                                FastAPI custom signup/login, bcrypt
                                      password hashing, JWT sessions

  Database                            Supabase PostgreSQL

  Backend                             Python FastAPI

  Frontend                            Next.js

  Hosting                             Vercel where practical; local
                                      development must work

  Theme                               Light cream + rich green + accent;
                                      dark black + rose-gold

  Demo data                           Synthetic and visibly labelled

  Roles                               Learner, Teacher
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 5. Riddle / Requirement Traceability

### Riddle 1 --- Same mark, different understanding

Implemented by the flawed-explanation investigation and teacher evidence
view. A learner must demonstrate reasoning through identifying and
explaining flaws rather than receiving only a correctness score.

### Riddle 2 --- Same wrong answer, different causes

Implemented by competing hypotheses, evidence scoring, confidence,
uncertainty and learner disagreement.

### Riddle 3 --- One informative next thing

Implemented by candidate follow-up scoring using predicted answer
divergence and burden penalty. The highest-scoring candidate is selected
and the interface explains why.

### Riddle 4 --- Familiarity is not retention

Implemented by changed-context transfer, independent no-tool assessment,
synthetic delayed checks and failure-triggered re-diagnosis/support
adaptation.

------------------------------------------------------------------------

## 6. Users and Permissions

### Learner

Can: - sign up/login; - view assigned learning investigation; - inspect
question/code/result/flawed explanation; - identify flawed parts; -
choose broad + specific issue category; - explain reasoning; - view
system hypotheses; - disagree and choose an alternative; - answer
selected follow-up; - complete support mini-lesson; - complete
transfer; - complete independent no-tool check; - view own
progress/evidence; - view synthetic delayed checks.

Cannot: - edit system rules; - alter scores/evidence; - see other
learners' private data; - access teacher controls.

### Teacher/Mentor

Can: - view learner evidence; - view hypotheses and confidence; - see
learner disagreements; - see follow-up selected and rationale; - inspect
support/transfer/independent/delayed evidence; - see adaptation
events; - distinguish synthetic records from live records.

Cannot: - silently rewrite learner evidence; - turn the product into a
leaderboard; - claim synthetic delayed results are real longitudinal
observations.

------------------------------------------------------------------------

## 7. End-to-End Learner Journey

### Step 1 --- Investigation

Show: - problem statement; - relevant code; - expected output/result; -
flawed explanation; - explanation issue markers.

Learner selects flawed segment(s), chooses a broad diagnosis category,
then a specific reason, and writes a short explanation.

### Step 2 --- System interpretation

The rules engine evaluates the learner evidence against the exercise's
hypothesis pool.

Display: - leading hypothesis; - alternative hypothesis(es); -
confidence; - evidence supporting/contradicting each; - explicit
unknown/inconclusive state where appropriate.

### Step 3 --- Challenge

Learner sees: **Agree / I disagree**

If disagreeing: - choose an alternative interpretation; - optionally
explain why; - store the disagreement as evidence; - flag it in teacher
view.

### Step 4 --- Follow-up selection

Generate/evaluate candidate follow-ups.

For each candidate: - estimate predicted answer for each currently
plausible hypothesis; - calculate answer divergence; - subtract burden
penalty; - reject candidates that are redundant, already answered, or
invalid.

Select highest score.

Show a collapsible **Why this question?** panel: - current leading
hypotheses; - what differs between their predictions; - why this
follow-up distinguishes them; - what the system will learn from the
answer.

If no candidate provides meaningful separation, say the evidence is
inconclusive and use the lowest-burden pedagogically safe next step.

### Step 5 --- Targeted support

Provide an interactive mini-lesson: 1. concise explanation targeted to
the diagnosed issue; 2. worked example; 3. learner prediction/choice; 4.
immediate feedback; 5. record response.

### Step 6 --- Transfer

Present a new code problem in a changed context while testing the same
underlying concept.

No reuse of the original wording.

### Step 7 --- Independent check

Present a new short problem with: - no hints; - no support tools; -
solve task; - short explanation field.

Evaluate both result and explanation.

### Step 8 --- Delayed retention

Show two clearly labelled synthetic historical records: - approximately
one-month-old PASS; - approximately one-month-old FAIL.

These are demo records, not observed real retention.

### Step 9 --- Adaptation

For a failed delayed/independent check: 1. reopen competing hypotheses;
2. incorporate new evidence; 3. update confidence; 4. select a different
support intervention; 5. create a new verification task; 6. record the
adaptation event.

------------------------------------------------------------------------

## 8. Diagnostic Model

### Broad diagnosis categories

-   Concept
-   Logic
-   Execution
-   Output
-   Missing case

### Example specific reasons

Specific reasons are exercise-configurable and may include: -
variable/state misunderstanding; - condition/boolean misunderstanding; -
loop iteration misunderstanding; - execution-order misunderstanding; -
output prediction error; - edge-case/missing-case misunderstanding.

The UI must not assume every exercise has every reason.

### Hypothesis structure

Each hypothesis contains: - id; - label; - description; - target
concept; - supporting evidence rules; - contradicting evidence rules; -
related support; - distinguishing follow-ups; - transfer task mapping; -
independent task mapping.

### Confidence

Use a normalized deterministic score. Suggested implementation:

`raw_score = prior_weight + supporting_evidence - contradicting_evidence - unresolved_penalty`

Normalize active hypotheses to percentages.

Confidence labels: - **High:** \>= 0.75 - **Medium:** 0.50--0.74 -
**Low:** \< 0.50

If the top two hypotheses are too close (recommended margin \< 0.15),
show **Uncertain** rather than overstate confidence.

The UI must expose the evidence behind the score.

------------------------------------------------------------------------

## 9. Follow-up Algorithm

Each candidate follow-up defines predicted response classes for relevant
hypotheses.

### Divergence

For hypotheses h1...hn, calculate the disagreement of their predicted
response distributions.

For a simple deterministic implementation:

`divergence = count(distinct predicted_answer_class) / count(active_hypotheses)`

Then:

`selection_score = divergence * 100 - burden_penalty`

Recommended burden values: - 0 = one-click/very short; - 5 = short
text; - 10 = moderate code reasoning; - 20 = multi-step task.

Tie-break: 1. higher divergence; 2. lower burden; 3. fewer seconds/steps
estimated; 4. authored priority.

The selected candidate must have a meaningful rationale.

------------------------------------------------------------------------

## 10. Support Rules

Support must map to the current leading hypothesis, not generic "study
harder" advice.

Example mappings: - loop iteration issue → trace-table mini-lesson; -
condition/boolean issue → condition evaluation mini-lesson; -
state/variable issue → variable-state walkthrough; - execution-order
issue → line-by-line execution prediction; - output prediction issue →
predict-then-run example.

Support is successful only if the learner completes the interactive
check; merely opening support is not success evidence.

------------------------------------------------------------------------

## 11. Transfer and Independent Evaluation

### Transfer

Must differ in: - variable names; - surrounding scenario; - code
structure; - surface wording.

Must preserve: - underlying concept; - intended misconception/hypothesis
being tested.

### Independent check

Must be: - unseen; - no hints; - no support; - no answer reveal; - short
enough for focused reasoning.

Record: - correctness; - explanation; - explanation evidence tags; -
duration if available; - resulting hypothesis evidence.

Do not reduce all evidence to one score.

------------------------------------------------------------------------

## 12. Teacher View

Teacher dashboard should prioritize evidence over ranking.

For each learner: - current learning state; - latest investigation; -
learner response; - evidence; - hypothesis ranking; -
confidence/uncertainty; - learner disagreement; - follow-up chosen; -
"Why this question?" rationale; - support completed; - transfer
result; - independent result; - delayed synthetic results; - adaptation
history.

Visual warning: **Synthetic demo data** must be visible wherever seeded
historical checks appear.

No class leaderboard.

------------------------------------------------------------------------

## 13. Pages

### `/`

Landing page: - product thesis; - concise R1→R4 journey; - Login / Sign
up; - demo disclaimer.

### `/login`

Username + password.

States: - loading; - invalid credentials; - locked/disabled account; -
network error.

### `/signup`

Username + password + confirm password + role.

Validation: - required; - username length; - password minimum; -
password match; - duplicate username.

### `/learner`

Learner home: - current investigation; - progress through journey; -
delayed-check card; - evidence summary.

### `/investigate/:id`

Main investigation page: - question; - code; - expected result; - flawed
explanation; - structured issue selection; - explanation input.

### `/diagnosis/:id`

Hypotheses: - ranked explanations; - evidence; - confidence; -
agree/disagree; - alternative selection.

### `/follow-up/:id`

Selected question + Why this question? - answer input; - submit; -
inconclusive state.

### `/support/:id`

Interactive mini-lesson.

### `/transfer/:id`

Changed-context new-code task.

### `/independent/:id`

Fresh problem + explanation; no tools/hints.

### `/retention/:id`

Synthetic historical checks and adaptation status.

### `/teacher`

Teacher learner list.

### `/teacher/learners/:id`

Evidence timeline and investigation details.

------------------------------------------------------------------------

## 14. UI States

Every page requiring data must implement: - loading skeleton; - empty
state; - recoverable error state; - disabled/submit state; - success
state; - validation state.

Avoid silent failures.

Use accessible labels, keyboard navigation, visible focus states and
sufficient contrast.

------------------------------------------------------------------------

## 15. Design System

### Light

-   background: warm cream;
-   primary: rich green;
-   accent: restrained secondary accent;
-   text: near-black;
-   cards: warm white;
-   borders: muted neutral.

### Dark

-   background: near-black;
-   primary: green;
-   accent: rose-gold;
-   cards: charcoal;
-   text: warm white.

Use CSS variables/design tokens rather than scattered hex values.

Animations: - short page transitions; - progress transitions; -
accordion expand/collapse; - success feedback.

No decorative animation that competes with reasoning tasks.

------------------------------------------------------------------------

## 16. Database Requirements

Core tables:

### users

-   id UUID PK
-   username UNIQUE
-   password_hash
-   role enum learner/teacher
-   created_at
-   updated_at

### learner_profiles

-   id UUID PK
-   user_id FK users
-   display_name
-   created_at

### concepts

-   id UUID PK
-   slug UNIQUE
-   name
-   description

### exercises

-   id UUID PK
-   concept_id FK
-   title
-   prompt
-   code
-   expected_output
-   flawed_explanation
-   active
-   created_at

### explanation_segments

-   id UUID PK
-   exercise_id FK
-   segment_order
-   text
-   is_flawed
-   issue_broad_category
-   issue_specific_reason

### hypotheses

-   id UUID PK
-   exercise_id FK
-   key
-   label
-   description
-   prior_weight
-   support_content_id nullable

### evidence_rules

-   id UUID PK
-   hypothesis_id FK
-   evidence_key
-   polarity
-   weight

### follow_ups

-   id UUID PK
-   exercise_id FK
-   prompt
-   answer_type
-   burden_score
-   explanation
-   active

### follow_up_predictions

-   id UUID PK
-   follow_up_id FK
-   hypothesis_id FK
-   predicted_answer_class

### attempts

-   id UUID PK
-   learner_id FK
-   exercise_id FK
-   stage
-   started_at
-   completed_at
-   status

### learner_evidence

-   id UUID PK
-   attempt_id FK
-   evidence_key
-   value_json
-   source
-   created_at

### hypothesis_assessments

-   id UUID PK
-   attempt_id FK
-   hypothesis_id FK
-   score
-   confidence_label
-   evidence_summary
-   created_at

### learner_challenges

-   id UUID PK
-   attempt_id FK
-   system_hypothesis_id FK
-   alternative_hypothesis_id FK
-   learner_reason
-   created_at

### follow_up_selections

-   id UUID PK
-   attempt_id FK
-   follow_up_id FK
-   divergence_score
-   burden_penalty
-   final_score
-   rationale
-   created_at

### support_modules

-   id UUID PK
-   hypothesis_id FK
-   title
-   explanation
-   worked_example
-   prediction_prompt
-   choices_json
-   correct_choice
-   feedback_correct
-   feedback_incorrect

### support_attempts

-   id UUID PK
-   attempt_id FK
-   support_module_id FK
-   selected_choice
-   correct
-   completed_at

### transfer_tasks

-   id UUID PK
-   concept_id FK
-   prompt
-   code
-   expected_output
-   explanation_prompt

### transfer_attempts

-   id UUID PK
-   learner_id FK
-   transfer_task_id FK
-   answer
-   explanation
-   correct
-   completed_at

### independent_tasks

-   id UUID PK
-   concept_id FK
-   prompt
-   code
-   expected_output
-   explanation_prompt

### independent_attempts

-   id UUID PK
-   learner_id FK
-   task_id FK
-   answer
-   explanation
-   correct
-   evidence_json
-   completed_at

### retention_checks

-   id UUID PK
-   learner_id FK
-   concept_id FK
-   check_date
-   is_synthetic
-   outcome
-   prompt
-   code
-   expected_output
-   explanation
-   adaptation_required

### adaptation_events

-   id UUID PK
-   learner_id FK
-   source_check_id FK
-   old_assessment_json
-   new_assessment_json
-   support_module_id FK
-   verification_task_id nullable
-   reason
-   created_at

Add indexes for user username, learner_id, exercise_id, attempt_id,
hypothesis_id and timestamps.

------------------------------------------------------------------------

## 17. API Contract

Use REST JSON.

### Auth

-   `POST /api/auth/signup`
-   `POST /api/auth/login`
-   `POST /api/auth/logout`
-   `GET /api/auth/me`

### Learner

-   `GET /api/learner/home`
-   `GET /api/investigations/:id`
-   `POST /api/investigations/:id/correction`
-   `GET /api/investigations/:id/diagnosis`
-   `POST /api/investigations/:id/challenge`
-   `POST /api/investigations/:id/select-follow-up`
-   `POST /api/investigations/:id/follow-up`
-   `GET /api/investigations/:id/support`
-   `POST /api/investigations/:id/support`
-   `GET /api/investigations/:id/transfer`
-   `POST /api/investigations/:id/transfer`
-   `GET /api/investigations/:id/independent`
-   `POST /api/investigations/:id/independent`
-   `GET /api/retention`
-   `POST /api/retention/:id/adapt`

### Teacher

-   `GET /api/teacher/learners`
-   `GET /api/teacher/learners/:id`
-   `GET /api/teacher/learners/:id/timeline`

All protected endpoints require JWT authentication and server-side role
checks.

------------------------------------------------------------------------

## 18. Security

-   Never store plaintext passwords.
-   Use bcrypt/argon2-compatible password hashing; bcrypt is the locked
    implementation choice.
-   JWT secret only in environment variables.
-   Never commit `.env`.
-   Validate all request bodies.
-   Parameterized DB access / ORM.
-   Server-side authorization on every protected resource.
-   Learners may access only their own records.
-   Teachers may access only permitted learner records.
-   Do not trust role fields sent by the client.
-   Sanitize rendered learner text where required.
-   Do not expose internal scoring secrets unnecessarily.

------------------------------------------------------------------------

## 19. Seed Data

Create synthetic demo data for at least: - Learner A: correct-but-lucky
evidence; - Learner B: incorrect with a clear misconception; - Learner
C: incorrect but reasoning indicates partial understanding; - one
learner with disagreement; - one learner with delayed PASS; - one
learner with delayed FAIL and adaptation.

Use basic programming concepts: - variables/state; - conditionals; -
loops.

All seeded retention records must have `is_synthetic=true`.

------------------------------------------------------------------------

## 20. Error Handling

API errors use consistent shape:

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": {}
  }
}
```

Frontend must translate errors into useful actions.

Do not reveal database errors, stack traces or secrets to users.

------------------------------------------------------------------------

## 21. Testing Requirements

### Unit

-   hypothesis scoring;
-   confidence normalization;
-   uncertainty threshold;
-   follow-up divergence;
-   burden penalty;
-   tie-breaking;
-   adaptation selection.

### API

-   signup/login;
-   authentication;
-   authorization;
-   learner isolation;
-   teacher access;
-   investigation submission;
-   challenge;
-   follow-up;
-   support;
-   transfer;
-   independent;
-   retention/adaptation.

### UI

-   every major page renders;
-   validation states;
-   loading/empty/error states;
-   theme toggle;
-   keyboard navigation.

### End-to-end

One complete learner path must work:

**login → investigate → diagnose → disagree → follow-up → support →
transfer → independent → retention → adaptation**

Acceptance requires that seeded demo data makes the R1→R4 journey
visibly demonstrable.

------------------------------------------------------------------------

## 22. Acceptance Criteria

The project is complete when:

1.  A learner can complete the full investigation journey without manual
    database edits.
2.  The flawed explanation investigation captures structured evidence.
3.  At least two competing hypotheses can remain plausible.
4.  Confidence and uncertainty are visible.
5.  Learner disagreement is persisted and visible to teachers.
6.  Follow-up selection is deterministic and explainable.
7.  "Why this question?" shows a meaningful rationale.
8.  Support is interactive, not a static article.
9.  Transfer changes context and code.
10. Independent check is unseen, tool-free, and requires explanation +
    solution.
11. A failed check changes diagnosis/support rather than merely showing
    "try again."
12. Synthetic delayed records visibly demonstrate PASS and FAIL.
13. Teacher view shows evidence rather than a leaderboard.
14. No LLM is required for core functionality.
15. No plaintext passwords or committed secrets exist.
16. Seed/demo data is clearly labelled synthetic.
17. README contains setup/run instructions, architecture summary, riddle
    mapping, limitations and Frontend Pack reference.
18. The application works locally using the documented environment
    variables and setup.

------------------------------------------------------------------------

## 23. Demo / Judging Narrative

The strongest demo should follow one learner rather than jumping across
unrelated screens:

1.  Show the same score can hide reasoning.
2.  Learner catches the flawed explanation.
3.  System presents multiple plausible causes.
4.  Learner challenges the system.
5.  System chooses the most informative next question and explains why.
6.  Targeted support teaches the specific issue.
7.  Learner succeeds on changed-context transfer.
8.  Learner must independently solve and explain a new problem.
9.  Show synthetic delayed PASS and FAIL.
10. Use the FAIL to demonstrate re-diagnosis and changed support.

Never say seeded data proves real month-long retention.

------------------------------------------------------------------------

## 24. Deliverables Around the PRD

The implementation package should include: - this PRD; - TRD; -
README; - `AGENTS.md`; - screenshot/caption list for Frontend Pack; -
two-minute demo script; - debate/Q&A cheat sheet.
