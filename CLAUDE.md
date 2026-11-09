# Claude Code Project Instructions

Project: **An LLM Copilot for Verilog Design** — Rutgers ECE Capstone, Group 62, four undergraduate ECE students. Faculty advisor: Professor Hang Liu. Planning baseline: November 8, 2026.

## Initial role

Claude Code initially focuses on **implementation**. Codex initially focuses on architecture, task planning, review, and testing. Either tool may perform other tasks when explicitly assigned. Do not implement the full application in response to the initial documentation task.

When assigned implementation, complete only the agreed milestone and its acceptance checks, provide concrete review evidence, and hand off files before Codex edits them. Begin with the offline M1 harness when assigned; do not expand directly into providers, repair orchestration, or full benchmark campaigns.

## Shared project contract

Read these before changing project files:

1. [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md) — requirements, evaluation protocol, and **section 5: shared engineering and collaboration rules**.
2. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — component boundaries, contracts, execution policy, and artifacts.
3. [docs/DECISIONS.md](docs/DECISIONS.md) — confirmed decisions, proposals, and unresolved questions.
4. [docs/ROADMAP.md](docs/ROADMAP.md) — assigned milestone, acceptance evidence, and exact-file ownership ledger.
5. [docs/TEAM_ROLES.md](docs/TEAM_ROLES.md) — engineering owners and review responsibilities.

Both agent instruction files point to the same normative rules; neither defines a separate architecture. Keep this shared-contract section identical in `AGENTS.md` and `CLAUDE.md` when changing it. Explicit team assignments can change initial tool roles; do not silently reinterpret unresolved technical proposals as confirmed decisions.

- Work locally in the existing `Capstone` root and preserve unrelated files. No nested project directory, GitHub repository creation, remote creation, or push is authorized.
- Claim exact files in the roadmap ledger before edits. Never allow two agents to modify the same file simultaneously, including documentation, configuration, contracts, and tests. Hand off ownership before reviewer fixes.
- Use small milestones and the documented interfaces. Avoid unnecessary frameworks or infrastructure. Provider SDKs remain in provider adapters, tool execution in the runner, and benchmark details in benchmark adapters.
- Never modify trusted benchmark testbenches/checkers or reference expectations to make incorrect RTL pass. Keep private verification/reference source out of model prompts.
- Never claim code was tested unless the checks ran. Report exact commands and distinguish mocked/live, executed/skipped, and passed/failed results.
- Assume no API keys or GPUs. Keep offline mock/replay operation possible and never store credentials in code, prompts, logs, or artifacts.
- Bound subprocesses, requests, retries, repair attempts, and artifacts. Follow the execution-isolation gate in ARCHITECTURE before running arbitrary generated RTL.
- Record important decisions and actual evidence in DECISIONS. Invent no faculty requirements, approvals, deadlines, or performance results.
- At each handoff, list changed files, validation results, limitations, and the next bounded task; release ownership after editing stops.

### Permanent review workflow

1. Every formal code review or milestone re-review MUST be saved as a Markdown report under `docs/reviews/`.
2. Save the report automatically as part of the review task, before the final response, without waiting for a separate user request. Apply the existing exact-file ownership rules to the report, index, and any required ledger entry.
3. Use a unique filename with the milestone and review round, such as `M1_REVIEW_R1.md`, `M1_REVIEW_R2.md`, or `M2_REVIEW_R1.md`. Consult [docs/reviews/README.md](docs/reviews/README.md) and existing files to choose the next unused round. Preserve legacy filenames already in the history.
4. Never overwrite or delete historical reviews. A correction or changed verdict belongs in a new report that links to the earlier report; update the history index without erasing earlier entries.
5. Every report must include its date, milestone, review round, verdict, independently executed test commands/results (including skips or tests not run), findings with severity, and concrete action items. Include relevant file/line references, evidence, limitations, and re-review acceptance criteria. Use `APPROVED`, `APPROVED WITH NON-BLOCKING ISSUES`, or `CHANGES REQUIRED` for the verdict.
6. Distinguish verified findings and executed evidence from assumptions, reported-but-unverified claims, and untested risks. Follow the existing rule against claiming unexecuted tests passed.
7. When reviewing fixes, explicitly track each previously identified issue as **fixed**, **unresolved**, or **deferred**, with supporting evidence or the reason for deferral. Preserve issue IDs and distinguish implementation claims from independently verified closure.
8. A review-only task may create or update review documentation (including its history index and required ownership ledger entries), but must not modify application code. Historical reports remain immutable; fixes require a separate implementation assignment and ownership handoff.
9. Claude Code must read the latest applicable review report, located through the history index, before implementing review fixes. Read linked earlier reports when needed to understand issue IDs or acceptance criteria.
10. After completing milestone corrections, Claude Code must save a uniquely named implementation handoff summary under `docs/reviews/`, for example `M1_HANDOFF_R2.md` for corrections addressing R2. Include the date, addressed report, exact changed files, issue-by-issue claimed status, executed commands/results, evidence artifacts, remaining limitations, and released ownership. Never overwrite an earlier handoff; use a unique suffix for additional handoffs addressing the same round and link them from the index. A handoff is not an independent review or technical approval.
11. Codex must independently verify fixes before a milestone is considered technically approved, then save the verification as the next review report and update the index. Implementation handoffs or passing tests reported by another agent do not establish independent approval.
12. Technical approval does not replace team approval for major architectural decisions. Record adopted choices through `docs/DECISIONS.md`; reviewer recommendations remain recommendations until appropriately adopted.

Keep this workflow identical in `AGENTS.md` and `CLAUDE.md`. Treat the history index as navigation and current-status guidance; the dated reports retain the evidence and verdict at each review snapshot.

The first proposed implementation assignment is **M1: offline verification harness** in ROADMAP. Its commands and package paths are design targets until implemented; do not report them as existing features.
