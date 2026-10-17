# Final review findings — 2026-10-17

The independent review found four issues. The following causes were confirmed in source before changes.

1. Support submission immediately changed stage, while `state.result` retained authored feedback. The shared journey banner rendered it during adapted independent checks. Keep completed support and its feedback on the support screen until an explicit continue action; exclude prior teaching/interpretation context from independent responses.
2. Stage validation alone did not distinguish successive support or independent tasks. A stale tab could submit an earlier response in a later adaptation cycle. Require the displayed module/task ID and validate it under the existing attempt lock, returning 409 before recording evidence.
3. Starting an investigation checked then inserted without a shared lock. Concurrent starts could both observe no existing attempt. Lock the learner row before checking active attempts so concurrent requests resume the same investigation.
4. The teacher endpoint stored complete evidence snapshots, but the UI omitted hypothesis labels, supporting/contradicting observations, disagreement labels, and old adaptation assessments. Resolve disagreement labels server-side and render both preserved assessments and evidence.

Regression coverage will exercise adapted incorrect support feedback, stale support/task submissions, concurrent starts, and teacher evidence visibility. No database reset or evidence rewrite is required.

The first teacher browser assertion matched supporting observations inside a deliberately collapsed comparison panel. The ordinary interpretation event was rendered correctly. Scope the assertion to an Interpretation event, then separately open and verify the comparison. This is a test-locator correction.

During the support UI edit, the Windows shell pipeline replaced a literal arrow in a replacement string, leaving a missing JSX closing brace. TypeScript caught it before the browser run. Rewrite the component with a structured patch and verify typecheck/lint. Generated text artifacts use explicit UTF-8; subprocess commands use the absolute virtual-environment interpreter because Windows does not resolve an executable relative to a subprocess working-directory argument.
# Classroom review — 2026-10-17

The final review found three recovery defects. A quiz request error offered a reload that unmounted uncontrolled answer fields; retain answers/reasoning in component state so loading and retry do not erase them. SQLAlchemy sessions retain objects after commit, so an initial grading claim could read cached pending status despite obtaining a row lock; refresh with populate_existing while locking. A malformed Gemini envelope could raise AttributeError outside the expected provider error handler and leave a grading lease active; normalize it to INVALID_FEEDBACK. Transport regression tests reproduced both malformed-envelope cases before fixing them.

## Hackathon release review

The independent review identified three evidence gaps. Delayed checks projected no provenance after a demonstration account was reclassified; the API now derives provenance from the account and original attempt, hides sample checks from learner history, and labels teacher records. Teacher delayed-check summaries omitted submitted explanations; assigned teachers now receive completed responses and results while future tasks and answer keys remain private. The new course progress summary needs an upgrade backfill; it was run against the existing schema and is documented in setup instructions.

The isolated production build directory was absent from ESLint ignores, so a subsequent lint traversed generated bundles and reported generated-code violations. Add `.next-release/**` alongside `.next/**`; source rules remain unchanged. A frontend feedback limit of 3000 also exceeded the server limit of 2000; the form now matches the server contract.

Release packaging validation found caption/transcript checksum mismatches after Git normalized text line endings. Recompute hashes from the final checkout and verify both remote downloads and ZIP members. The PDF/MP4 are explicitly binary in `.gitattributes` and retain exact bytes. Next.js regenerates `next-env.d.ts` with different paths for development and release output, so it is now ignored/untracked as the installed Next.js guide recommends; typecheck first runs `next typegen`.

## Classroom reliability extension

Teacher review previously required an AI-graded submission, and effective feedback returned early when AI output was missing. This prevented teachers from assessing already saved student responses during an outage. The server now permits assigned teachers to append assessments to saved responses, combines only assessed questions, and preserves teacher overrides if AI completes later. Unassessed questions are not counted as zero. Regression tests cover ownership, partial/full assessment, and a teacher assessment committed while an AI request is in flight.

Independent review found that classroom quiz cards still used the raw AI status after a complete teacher assessment. The classroom projection now includes assessment progress from a batched review query, and cards distinguish saved answers, partial feedback, and ready feedback. Both backend projection assertions and browser presentation fixtures cover these states.

Final inspection found that the assessment projection reused `total`, overwriting the query's quiz count with the response count. The regression reproduced two quizzes reported for a one-quiz, two-question submission. Give the response count its own variable and retain the database count for pagination.

Journey inputs lived only in uncontrolled form elements, so a refresh discarded unfinished reasoning. A bounded, tab-scoped draft store now uses the authorized attempt, stage and task identifiers. New retry tasks have distinct keys; successful submission and sign-out clear the appropriate drafts. Storage failures do not block learning. Browser tests cover refresh, request failure, retry isolation and unavailable storage.

The teacher dashboard loaded an entire assigned roster. Its new endpoint filters and pages in PostgreSQL before counting attempts for visible students; the existing array endpoint remains compatible. Search escapes SQL wildcard characters and preserves teacher assignment scope. The UI reuses existing design tokens and offers an explicit sample-account filter. API and browser regressions cover pagination, search, role checks and empty results.

## Recovery and invitation controls

A controlled browser regression reproduced stale quiz cards after selecting the next page: the shared resource hook changed the request URL without invalidating the previous result or showing loading. The page label advanced while old records remained actionable. Resource results must be associated with their request path and reload revision; render loading until that exact request settles, hide prior errors/data, and ignore mutation setters from an obsolete request. The regression also exercises a failed page request and successful retry.

Independent review found that retrying AI feedback on a later teacher response page assigned the mutation response's default first page to the current page. The retry now reloads the current paginated GET. A controlled browser regression verifies that the second-page student remains visible and the first-page student does not replace them.

Quiz drafts previously lived only in React state. A refresh regression reproduced lost reasoning before adding learner/quiz/question-scoped tab storage. Final review caught a blocked-storage regression when retrying a failed request unmounted the new uncontrolled form. A failing browser test confirmed it; a bounded hook-local memory cache now preserves same-page retries even when storage writes fail. A full browser refresh still cannot recover when storage is unavailable. Successful submission and authoritative submitted loads clear memory and storage; sign-out clears stored drafts and unmounts the page cache.

Reusable invitations had no teacher-managed replacement operation. Replacement now locks the teacher's invitation row and requires the currently displayed code. A stale or simultaneous replacement cannot silently replace a newer code. Signup uses the same row lock, so a lookup waiting behind a committed replacement rejects the old code. The other code, earlier accepted accounts and existing enrollments remain intact. PostgreSQL tests exercise both code types, repeat enrollment, permission checks, competing replacements and signup waiting behind rotation.

Two new browser assertions initially matched Next.js's route announcer as well as application alerts. The locators now target the error panel or invitation region. This was a test ambiguity, not a product error; application behavior is tested separately from the framework announcement element.
