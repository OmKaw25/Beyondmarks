# Agent Rulebook (agents.md)

This document serves as the permanent rulebook for AI coding agents working on the Beyond Marks project (Understanding Learner Reasoning and Enabling Lasting Learning). These rules override any default behaviors and are non-negotiable.

## 1. Ask, Don't Guess (The Golden Rule)
- Ask as many questions as needed, at any point, about anything. There is no such thing as "too many questions."
- If there is even the smallest doubt about what to build, how to build it, which option to pick, or how to interpret something in `beyond-marks-prd.md`, `beyond-marks-trd.md`, or `workflow.md` — **STOP and ask the user (Om)**.
- Do not guess. Do not assume. No guessing work, ever, on anything not explicitly and unambiguously covered by the project documents. This applies to every kind of decision: technical, design, scope, and data.

## 2. No Silent Workarounds or Requirement Modifications
- If a step in `workflow.md` cannot be completed as described (e.g., a dataset isn't available, the Supabase database isn't accessible), do NOT default to a workaround on your own.
- **Stop and ask Om how to proceed.**
- If asked for alternatives, propose realistic options and wait for a choice.
- Only build a mock/stub if explicitly approved, and clearly mark it as such in code comments (`# MOCK: ...`).
- Do not skip, remove, or silently alter any requirement listed in `beyond-marks-prd.md` or `beyond-marks-trd.md`. If a conflict arises between `workflow.md` and the PRD/TRD, flag it rather than deciding independently.

## 3. Strict Root Cause Analysis (RCA) on Errors
- When hitting an error or something breaks, perform a **Root Cause Analysis (RCA) first**.
- Do not just patch symptoms or retry blindly.
- Document the RCA (what broke, why, what was checked) before applying a fix.
- If an issue persists after your RCA and initial fix attempt, **do not keep retrying on your own** — stop and ask Om, showing the RCA so far.

## 4. Phase-by-Phase Checkpoints
- Follow the phases in `workflow.md` strictly in order. Do not skip ahead or combine phases.
- After completing each phase, **stop and summarize**:
  - What was built
  - What's still mocked/pending
- **Ask for confirmation** before moving to the next phase.

## 5. Design and Consistency Check
- Every new UI component must be checked against `design.md` before styling.
- If a needed visual value is missing from `design.md`, do not invent one — ask Om and add it to the file.
