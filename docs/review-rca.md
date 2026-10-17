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
