# Python command resolution — 2026-10-17

## Seed-history browser selector after automatic enrollment

The full browser run passed 10 checks, including the new classroom flow, but the old sample-history test opened the first assigned learner alphabetically. Automatic enrollment now correctly adds real test learners ahead of learner_a, so it inspected a different person's evidence and could not find the sample adaptation. Select the intended learner_a card by its heading. No product data or authorization change is needed.

## Mobile teacher result width

The live browser flow completed AI grading and recommendation ordering, then failed the teacher-results viewport check at 390px. DOM measurements showed the entire single-column grid expanded to 392px: a long student username beside the AI-feedback badge imposed an intrinsic minimum. Permit the main grid item to shrink and section-heading rows to wrap. Preserve the existing spacing/color tokens and rerun the live browser flow.

## Draft editor type-check failure

TypeScript caught `initial` referenced in CourseForm. A replacement intended to prefill the quiz title also matched the course-title input. CourseForm has no initial-quiz prop; remove that prefill only from CourseForm and retain it in QuizForm. No database or submitted content was affected. Also use direct UTF-8 patches for UI symbols: PowerShell's default pipeline encoding replaced newly inserted Unicode symbols with question marks.

## Gemini model availability — classroom integration

The first live structured grading request returned HTTP 404. Model discovery succeeded with the supplied key and still listed gemini-2.5-flash-lite. A minimal diagnostic request returned the precise cause: that model is unavailable to new users, and the provider recommends gemini-3.5-flash-lite. This is a model-access restriction, not a rejected key. Verify the replacement's free-tier pricing before changing the model setting and retrying the grading request.

## Visual capture timing — 2026-10-17

Inspection found the first Transfer screenshot captured a loading skeleton, and a dark screenshot caught a button partway through its theme-color transition. The helper waited only for the heading, which exists before data/authentication finish loading, and captured animations as-is. Update the capture helper to wait for loading indicators to disappear and the authenticated shell to resolve, then disable animations for the screenshot. This changes verification timing, not product behavior or palette.

## Database connection interruption during verification — 2026-10-17

The verification run lost both PostgreSQL connections while creating the isolated test schema (at the existing support_modules table, before migration 003 or any journey assertions). PostgreSQL reported an unexpectedly closed connection. The 31 non-integration checks passed. A fresh connection subsequently returned SELECT 1 and migration 0002; the generated schema contained zero tables, confirming transactional rollback. No application change is justified by this evidence. Remove only that empty generated test schema and rerun integration once against the recovered connection. The server-side reason for the disconnection is not established.

## What failed

A read-only documentation validation invoked through the bare `python` command failed with the Windows message that Python was not found.

## What was checked

- `Get-Command python` resolved to the WindowsApps execution alias.
- Standard per-user and Program Files Python directories did not reveal the runtime through the checked locations.
- `Get-Command py` found the Python launcher.
- `py --list` reported Python 3.14.6 and Python 3.11.9.
- `py -3.11 --version` successfully reported Python 3.11.9.
- The document checks were performed successfully in PowerShell.

## Cause and resolution

The bare `python` entry point is not resolving to the installed runtime in this shell. Python is installed and accessible through the launcher. Backend setup should explicitly use `py -3.11 -m venv .venv` and then use that environment's interpreter. No system PATH changes or runtime installation were necessary.

This was an environment command-resolution issue; no application code or tests existed at the time of the failure.

## Application configuration collision

The first API test collection failed because the host exports `DEBUG=release`. Pydantic mapped the generic environment variable to the app's boolean debug setting. The failing configuration regression test reproduces that collision. Use the explicit `BM_DEBUG` alias for the application setting; do not alter the host environment.

## Local frontend origin validation

Browser signup/login failed with HTTP 403 before reaching FastAPI. A temporary diagnostic showed Origin `http://127.0.0.1:3000`, Host `127.0.0.1:3000`, and NextRequest.nextUrl.origin `http://localhost:3000`. Next.js normalized the internal URL, so comparison to nextUrl rejected legitimate same-host requests. Compare the Origin URL host to the actual HTTP Host instead, require HTTP(S), and retain FastAPI's explicit allowed-origin list. Remove the diagnostic after confirming the cause. Add browser assertions for both accepted local origin and rejected foreign origin.

The same browser run found the test's generic alert locator also matched Next.js's route announcer. Scope the assertion to the application's error panel; no product behavior change is required for that locator correction.

## Repeated database test connection interruption

A full run again lost both connections during isolated seed setup, before assertions (496 seconds elapsed while the command host was delayed). The focused classroom integration had passed immediately before this run. Fresh SELECT 1 succeeds, public migration is 0005, and only the failed run schema contains 30 empty tables with zero users. No application behavior change is justified; clean up that exact generated schema and rerun serially after browser checks, recording any remaining infrastructure limitation.
