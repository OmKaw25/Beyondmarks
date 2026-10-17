# Beyond Marks Design Specification

**Status: Approved by Om on 2026-10-17.** This document turns the PRD's cream/green light theme and black/rose-gold dark theme into concrete values approved for implementation.

## Product experience

The interface should feel like a calm learning workspace. Keep the current task, supporting evidence, and next action legible. Show uncertainty and learner disagreement without suggesting failure or low ability. Avoid leaderboards, decorative achievement counters, and animated distractions.

The learner journey is: investigate → interpretation/challenge → one follow-up → support → transfer → independent check → retention/adaptation. The teacher view follows the same evidence chronologically.

## Color tokens

Om's dark-theme revision uses neutral near-black and charcoal surfaces, rose-gold primary actions, and restrained amethyst secondary accents. Green is reserved for small success indicators; it no longer tints the interface.

| Token | Light | Dark |
| --- | --- | --- |
| `--bg` | `#F6F3EB` warm cream | `#101011` near-black |
| `--surface` | `#FFFEFA` warm white | `#19181B` charcoal |
| `--surface-muted` | `#ECEFE5` | `#242126` |
| `--text` | `#182B23` | `#F3EEEA` |
| `--text-muted` | `#526158` | `#BDB3B7` |
| `--primary` | `#245C43` rich green | `#D6AA9A` rose gold |
| `--primary-hover` | `#184730` | `#E7C0B0` |
| `--on-primary` | `#FFFFFF` | `#211719` |
| `--accent` | `#8A4D36` restrained terracotta | `#B5A4D4` muted amethyst |
| `--border` | `#CAD2C5` | `#41363E` |
| `--success` | `#245C43` | `#A8BCA6` |
| `--warning` | `#805A13` | `#D6BA7F` |
| `--danger` | `#A13A34` | `#E7A0A4` |
| `--focus` | `#245C43` | `#E7C0B0` |

Contrast must be measured on the actual rendered combinations before acceptance. Borders supplement labels and grouping; color never carries meaning alone.

## Type, spacing, and dimensions

- Interface font: local system stack `Segoe UI, Arial, sans-serif`; no external font dependency.
- Code font: `Cascadia Code, Consolas, monospace`.
- Base body: 16px, line-height 1.6; secondary text 14px; labels 14px with weight 600.
- Main headings: 36px desktop / 28px mobile; section headings 24px; card headings 18px.
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64px.
- Page max-width: 1200px. Focused task column: maximum 760px.
- Page gutters: 32px desktop, 16px mobile. Card padding: 24px desktop, 16px mobile.
- Navigation sidebar: 232px on wide layouts. Collapse to a labelled mobile menu below 900px.
- Two-column evidence/task layouts stack below 900px.
- Minimum interactive height: 44px. Inputs and primary actions: 48px.
- `--radius-sm`: 8px; `--radius-md`: 14px; `--radius-lg`: 22px.
- `--shadow-sm`: `0 2px 10px rgb(0 0 0 / 5%)`.
- `--shadow-md`: `0 10px 30px rgb(0 0 0 / 8%)`.
- Focus outline: 3px solid focus token, 3px offset. Preserve visible focus in both themes.

## Shared components

### Teacher classroom extension

Keep teacher authoring compact: subject cards with expandable lessons, and an explicit Create quiz form containing topic, question, answer key, and optional reasoning guidance. Save as a draft before publishing to the class. Use existing card, two-grid, three-grid, form-stack, badge, notice, and button styles. Learners see published quizzes, saved answer/reasoning responses, separate answer and reasoning feedback, and courses ordered by their latest quiz evidence. Explain recommended priority in words; no ranking between students. Long lesson and answer text preserves line breaks. Both teacher codes are hidden behind Show class codes and have separate labels and copy actions.

Section headings and badges wrap on narrow screens, including long usernames in teacher results. The main grid item may shrink below its content's intrinsic width so it stays within the viewport.

### Learner history and sample data (Om's requested revision)

History is grouped by attempted topic, with only the latest non-synthetic attempt for each topic shown. Display the concept name, current step out of the seven journey steps, and Continue/Review action. Do not list individual stages or repeat earlier attempts as separate history cards.

The learner dashboard's "Your learning history" lists only actual activities, excluding `is_synthetic` attempts. The follow-up history likewise excludes synthetic checks. Seed account status does not add a technical banner to the learner dashboard. Sample records remain stored for deliberate demonstrations and teacher review, where a concise "Sample activity" label identifies them. Remove the technical synthetic-record sentence and leaderboard commentary from ordinary learner screens. This revision supersedes the earlier instruction to place long synthetic provenance banners in the normal learning flow; it does not relabel sample results as real achievements.

### Minimal neumorphic landing (Om's requested revision)

Om's follow-up requests more visual presence without more sections: scale the landing headline to 72px on desktop, fluidly down to 36–44px on phones; use 18px desktop supporting copy and a 64px desktop emblem. Journey labels use 16px with 14px descriptions. Enlarge the auth panel to 440px with 40px desktop padding and a 36px heading (32px on phones). These values supersede the smaller initial landing/auth dimensions below. Preserve the restrained layout, black/rose-gold dark palette, and soft surfaces.

Extend the authentication palette and soft shadow tokens to the landing page. Use one centered headline, one short description, one primary signup action, and four compact journey steps. Remove the nested demonstration cards, promotional strip, and duplicate signup section. The journey is a simple four-column row (two columns on phones) within the existing 760px focused width. Retain sign-in, theme switching, and the synthetic-demo disclosure. Use the existing 36px/28px headline scale and 16px/14px body scale.

### Minimal neumorphic authentication (Om's requested revision)

Login and signup use a single centered form, without the promotional column, quotation, or repeated headings. Keep the existing cream/green and dark palette. Authentication has a maximum 400px form width, 32px card padding (24px on phones), a 24px heading, 14px supporting text, and 48px controls. Match the card and controls to the page background. Use opposing soft shadows for a raised card/button and inset inputs: light shadows `#FFFFFF` / `#DEDAD0`; dark shadows `#242125` / `#070608`. Card shadows use 12px offsets and 32px blur; inputs use 3px offsets and 8px blur. Preserve visible labels, focus outlines, validation, teacher registration codes, and role-based login routing. The teacher code is requested only during signup.

### Application shell

Brand text "Beyond Marks", role label, theme toggle, and logout. Learner navigation exposes home and evidence history. Teacher navigation exposes assigned learners. Show current stage without ranking performance.

### Investigation workspace

Show the question, relevant code, expected result, and segmented flawed explanation before asking for a correction. Segments are selectable with explicit labels. Broad category limits available specific reasons. Explanation text has a persistent label and associated error.

### Interpretation cards

Each hypothesis shows its name, relative evidence score, confidence/uncertainty, and supporting/contradicting observations. Explain that deterministic confidence is not a calibrated probability of a learner's ability. Prominent actions: "This fits" and "I disagree". A disagreement records the learner's perspective without erasing the system assessment.

### Follow-up

One selected interaction and a collapsible "Why this question?" panel. The panel compares hypothesis predictions and explains what the response may distinguish. Inconclusive states explain the lack of useful separation and offer the safe next step.

### Support

Short explanation, worked example, prediction interaction, and immediate feedback. Feedback uses text and icons, not only color. Opening the lesson alone does not mark it completed.

### Verification

Transfer asks the learner to repair code in a new context using an authored line choice. Independent requires two results from a longer program without hints or earlier support. Reflect asks for a counterexample or boundary case that disproves a claim, plus a better rule. Each stage retains a written explanation and a structured reasoning choice; only the answer and structured choice are automatically assessed. Use the existing card, badge, code block, choice list, and two-column input styles and tokens. No additional visual tokens are needed. All seven steps are marked complete only after the reflection challenge passes. Failed verification returns to support and an unseen task of the same stage.

The workspace logo returns to `/learner` or `/teacher` according to the signed-in role and does not log out.

### Retention and adaptation

Every synthetic record displays "Synthetic demo record — not a real longitudinal observation" next to its date and result. A failed record can open the adaptation path. Show the earlier interpretation, new evidence, revised interpretation, changed support, and fresh verification task.

### Teacher evidence timeline

Show only assigned learners. Prioritize submitted reasoning, uncertainty, learner disagreement, follow-up rationale, support, verification, and adaptation. Separate synthetic records visibly from live work. No leaderboard or cross-learner score ranking.

## State and accessibility rules

- All data pages: loading skeleton, empty guidance, recoverable error with retry, and success state.
- All forms: persistent labels, required markers, validation messages linked by `aria-describedby`, submitting text, and disabled duplicate submission.
- Use semantic landmarks, headings, native buttons, and labelled controls.
- Announce submission errors and results with appropriate live regions.
- Keyboard users can select explanation segments and expand evidence/rationale panels.
- Code blocks preserve formatting and permit horizontal scrolling without breaking the viewport.
- Maintain the current server-confirmed stage on refresh. Do not fabricate progress when requests fail.
- Respect `prefers-reduced-motion`. Optional transitions use 160ms duration; no decorative looping motion.
- Theme changes replace tokens and persist preference; do not duplicate components.

## Acceptance review

Review landing, signup/login, the complete learner path, and teacher evidence at 390px and 1440px widths in both themes. Check text contrast, keyboard order, visible focus, empty/error states, loading behavior, and synthetic labels. Use `agents.md` for any proposed visual values absent from this specification.

## Classroom reliability interactions

- Reuse the existing card, form, button, grid, spacing and theme tokens for roster search and pagination; no new visual tokens are introduced.
- Show feedback readiness separately from AI processing status. Pending, partial and complete teacher assessments have distinct labels; unassessed questions do not display invented scores.
- Journey forms restore only the draft belonging to the current attempt, stage and task. A fresh retry starts blank. Draft recovery must not imply server submission.
- Quiz forms use the existing labelled answer/reasoning fields. Recovery belongs to the authenticated learner and exact quiz questions; do not display draft content as submitted feedback.
- Class-code replacement stays inside the existing hidden code panel. Use the current notice and button styles for explicit confirmation, cancellation, progress, conflict recovery and success. Explain that existing accounts remain enrolled and only the selected code changes.
- While loading a different page, show the loading state rather than the previous page's records under the new page number.
