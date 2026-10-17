# Judging questions and candid answers

**Who benefits?** Learners studying introductory programming and teachers who need to understand why a response happened. Teacher-created subjects extend the classroom lesson/quiz workflow beyond the authored programming investigations.

**What makes this more than a quiz?** Evidence survives across explanation, competing interpretations, a targeted probe, support, transfer, independent work and delayed observations. Learner disagreements and teacher corrections are first-class records.

**Is this diagnosing the learner?** No. Hypotheses are revisable explanations of a response. Relative weights are authored scores, not calibrated probabilities, psychological diagnoses or ability rankings. Time-pressure and unfinished-work context is self-report.

**Where is AI used?** Gemini provides formative feedback on written class-quiz answers and reasoning. The investigation's hypothesis scoring, probe selection and structured practice evaluation use deterministic rules. These are separate responsibilities.

**What if the AI is wrong?** A student can dispute feedback. Their assigned teacher can append corrected scores, feedback and a reason. Original AI output and the correction history remain visible. Corrected scores refresh course recommendations; unresolved feedback needing review does not drive ordering.

**Why these follow-ups?** Authored output, reading and unhurried probes have distinct predicted responses across hypotheses. The selector rewards separation and subtracts burden with stable tie-breaks. It exposes the rationale and falls back to general support if nothing usefully distinguishes the candidates.

**Can learners control the interaction?** They can report their perspective, challenge an interpretation, pause/resume the saved investigation and request teacher help. These actions remain in the evidence history.

**Does a correct independent answer prove independence?** No. The app hides current hints and answer keys, but cannot police external tools or earlier browser tabs. A supervised study is needed to substantiate independent performance.

**Is retention real?** The workflow is real: eligible non-demo completions persist checks due after 7 and 30 days, with fresh task snapshots, server-time enforcement, immutable submissions and failure adaptation. No month-long classroom outcome has yet been observed. Synthetic historical examples are separate and labelled.

**What happens when practice runs out?** Validated authored templates produce fresh variants for the three programming concepts, avoiding repeats across attempts. Failed practice returns to targeted support and a fresh check. Difficulty equivalence remains unvalidated; arbitrary teacher-created subjects do not receive these templates automatically.

**How is demo data kept honest?** Curriculum seeding creates no activity by default. Explicit demo seeding marks synthetic accounts/history. A clean pilot uses a separate schema with one provisioned teacher and no learners or outcomes. Other accounts remain unverified until their provenance is established.

**Can it handle a classroom?** Batched queries replace per-row lookups, course summaries avoid full-history reads, and quiz/submission/evidence lists are paginated. These measures have regression coverage; they are not a production load benchmark.

**What protects the data?** Scoped teacher assignments and learner ownership, bcrypt/JWT sessions, HttpOnly cookies, revocation, origin checks, database persistence and RLS against direct Supabase client access. Sensitive configuration stays in local ignored files. This is not a security certification.

**Is it hosted?** No working public deployment has been verified. The repository provides reproducible local setup, a captioned Frontend Pack and the recorded demonstration.

**What would a genuine pilot measure?** Educators should review content/rules first. With appropriate consent, record baseline reasoning, immediate transfer and independent performance, then actual 7/30-day observations. Evaluate false interpretations, learner disagreements and teacher corrections alongside completion and learning outcomes. Do not count automated or synthetic accounts as participants.

**Questions for another team:** How do you distinguish a lucky answer from understanding? What evidence would change your interpretation? Can a learner challenge it? What happens after support fails? Which results come from genuine elapsed time rather than simulated history?
