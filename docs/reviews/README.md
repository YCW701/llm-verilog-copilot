# Code Review History

Latest applicable M1 review: **[M1_REVIEW_R4.md](M1_REVIEW_R4.md)** — **APPROVED WITH NON-BLOCKING ISSUES** for publication of the preserved trusted-fixture baseline. R4 independently reran the suite on November 11, 2026 and retains R3's scoped approval and minor follow-ups. Model-generated RTL execution stays gated; technical approval does not adopt proposed team decisions. M2 was not started by the review.

The permanent workflow is defined identically in root [AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md). This index provides navigation; it does not replace report evidence or team decision records.

## Review reports

Outstanding issues in each row describe that review's snapshot, not a retrospective rewrite of its verdict. The latest report explicitly tracks closure of earlier issues.

| Milestone | Review round | Date | Report filename | Verdict | Outstanding blocking issues at that review |
| --- | --- | --- | --- | --- | --- |
| M1 | R1 (legacy filename) | 2026-11-08 | [M1_REVIEW.md](M1_REVIEW.md) | CHANGES REQUIRED (reported as not ready for approval) | M1-C1: forged checker pass; M1-C2: compiler signals classified as design failure; M1-C3: incomplete process cleanup. Important I1/I2 also required disposition. |
| M1 | R2 | 2026-11-08 | [M1_REVIEW_R2.md](M1_REVIEW_R2.md) | **CHANGES REQUIRED** | M1-C1 remains unresolved: lone-CR comment bypass yields a false pass. M1-I1 remains unresolved in version-probe capture. C2/C3 are independently verified fixed. |
| M1 | R3 | 2026-11-08 | [M1_REVIEW_R3.md](M1_REVIEW_R3.md) | **APPROVED WITH NON-BLOCKING ISSUES** | None for the qualified M1 scope. C1 and I1 fixes independently verified; C2/C3/I2 retained. Non-blocking follow-ups: M1-R3-N1 same-basename version-log collision; M1-R3-N2 verdict docstring clarification. |
| M1 | R4 — publication verification | 2026-11-11 | [M1_REVIEW_R4.md](M1_REVIEW_R4.md) | **APPROVED WITH NON-BLOCKING ISSUES** | None for the preserved default-tool baseline. Source/tests unchanged; 287 passed with Icarus, 239 passed / 48 skips without it. Existing minor wrapper/docstring issues deferred; manifest revision limitation disclosed. Final push/tag verification is reported in the publication handoff. |

`M1_REVIEW.md` is the original R1 report. Preserve its name and contents; do not rename, replace, or create a duplicate R1 solely to match the newer convention. The next M1 re-review should use the next unused round, normally `M1_REVIEW_R5.md`.

## Implementation handoffs

Implementation claims and ownership releases are also recorded in [ROADMAP.md](../ROADMAP.md); they are not independent approvals. After an assigned correction, Claude Code must save a unique handoff addressing the applicable report and add its link here. Keep implementation handoffs separate from independent review verdicts.

| Milestone | Addresses | Date | Handoff filename | Claimed status (not independently verified) |
| --- | --- | --- | --- | --- |
| M1 | R2 ([M1_REVIEW_R2.md](M1_REVIEW_R2.md)) | 2026-11-08 | [M1_HANDOFF_R2.md](M1_HANDOFF_R2.md) | Claims M1-C1 fixed (the R2 lone-CR bypass plus two newly found bypasses: backslash-CRLF string continuation and number-prefixed constructs). Claims M1-I1 fixed for version-probe capture. M1-R2-N1 addressed in documentation. Awaiting Codex re-review (`M1_REVIEW_R3.md`); M2 not started. |

The handoff row preserves its submitted claims. Independent disposition is now recorded in [R3](M1_REVIEW_R3.md): the reported corrections are verified within the stated M1 scope, with two non-blocking follow-ups. The historical handoff itself is unchanged.

## Maintaining this index

- Add every new formal review with its milestone, round, report filename, verdict, and outstanding blockers; update the latest-applicable link.
- Keep historical reports and their rows. Corrections and changed verdicts receive new uniquely named reports rather than edits to old reports.
- Link correction handoffs separately, naming the review round they address. Do not mark an issue independently fixed solely from an implementation claim.
- Claim this index and the exact new document paths through the existing ownership ledger before editing. Technical approval requires Codex's independent verification; major architectural decisions still require team approval.
