# Roadmap

Planning date: November 8, 2026. The original estimates below assumed four students working part time and are not course deadlines or advisor commitments. The current team has **three students** (updated November 11, 2026, academic year 2026–2027); ownership below follows the revised three-role TEAM_ROLES proposal, and future estimates/M2 assignments must be revisited before implementation. The historical rough total was 9–13 working weeks after kickoff. Parallel work uses disjoint files and agreed interfaces; elapsed estimates are not additive person-weeks.

## 1. Phases and acceptance gates

| Milestone | Approximate elapsed effort | Deliverable and gate | Dependencies / primary engineering role |
| --- | --- | --- | --- |
| M0 — Planning baseline | Current task | Five planning documents, aligned agent rules, decisions and open questions reviewed by the team. No application implementation. | Team; Role 1 coordinates. |
| M1 — Offline verification harness | 3–5 working days | Minimal package/CLI verifies team-authored RTL with Icarus and writes trustworthy structured evidence; acceptance details below. | M0; Roles 1 and 3. Claude Code implements; Codex reviews/tests. |
| M2 — Provider contract and one-shot path | 1–2 weeks | Mock provider works without credentials; deterministic extraction and interface validation; one-shot request→candidate→verification→artifacts. Two interchangeable adapters pass contract tests; live API smoke test only when access exists. Mock responses executed in M2 must be reviewed team fixtures. Executing any model-generated RTL requires the adopted execution-isolation policy first (DECISIONS M1-D5, Q05). | M1; Roles 1 and 2. |
| M3 — Bounded simulation-guided repair | 1–2 weeks | Failed canned responses followed by a correct one demonstrate repair lineage, sanitized feedback, all stop reasons, and no repair of infrastructure errors. Approve/validate execution isolation before the first execution of model-generated RTL (this gate applies in any milestone, not only M3); add live demonstration if access permits. | M2 and execution-policy decision; Roles 2 and 3. |
| M4 — Benchmark adapter and evaluation | 2 weeks | One pinned suite/subset passes known-good and known-bad qualification; immutable assets; frozen experiment manifest; independent-sample pass@1/pass@k and repair summaries validated on known counts. | M3 and benchmark/toolchain decisions; Roles 1 and 3. |
| M5 — Synthesis and timing | 1–2 weeks | Reproducible mapped area and constrained timing for passing candidates and references, units/coverage documented; failures and unavailable metrics explicit. Begin library/constraint feasibility spike earlier during M2. | M1 runner; M4 qualified candidates; Role 3, reviewed by Role 1. |
| M6 — Controlled experiments and delivery | 2–3 weeks | Freeze protocol; run one-shot, repair, and feasible budget-matched resampling; report metrics, cost/latency, coverage, failures, limitations, setup and replay instructions. Reproduce a stored result on a second teammate's environment. | M4/M5 and live model access; all roles. |
| M7 — Optional FPGA or extensions | Separate scope/estimate | Board/resource-specific demo, second benchmark, additional backend/provider, or UI only if core evaluation is complete and team agrees. | M6; no assumed hardware access. |

M1–M3 provide an offline functional demo, not completed benchmark research. Lack of model access can leave live experiments blocked while engineering continues. Do not replace real results with mock results. M5 area/timing is part of the core requirement; FPGA is the optional item.

### Progress (updated November 8, 2026, M1 closeout)

| Milestone | Status | Evidence / remaining gate |
| --- | --- | --- |
| M0 | Planning documents delivered. | Team review of the planning baseline is not recorded in these documents. |
| M1 | **Technically approved: APPROVED WITH NON-BLOCKING ISSUES** ([R3](reviews/M1_REVIEW_R3.md)) for team-authored RTL in the restricted subset on macOS / Python 3.14.6 / Icarus 13.0. | R3 ran the suite independently: 287 passed with Icarus; 239 passed + 48 labeled skips without it. The decisions DECISIONS M1-D1 to M1-D6 still await **team confirmation**. Two minor follow-ups are listed in section 5. Run artifacts (`runs/`) are local and not version-controlled. |
| M2 | **Not started.** | Needs a separate team assignment and ledger claim. Mock responses must be reviewed team fixtures. Model-generated RTL stays blocked until Q05 isolation is adopted (M1-D5). Q02 (provider access) gates live calls. |
| M3–M7 | Not started. | Gates as in the table above. |

Repository status (updated November 11, 2026): existing local M1 commit `7b4fbbe` is preserved. The team authorized integration with `https://github.com/YCW701/llm-verilog-copilot`, preserving its starter history, publishing `main`, and tagging the verified published baseline as `m1-baseline`. Publication execution evidence belongs in the current review/final handoff; this paragraph does not assert a push before it is verified. M2 remains unimplemented; its existing four-role plan requires staffing adjustment before a new assignment.

## 2. First implementation assignment for Claude Code: M1

**Objective:** verify a supplied, team-authored RTL file against a fixed miniature testbench using installed Icarus tools, and preserve structured evidence. Implement no LLM generation or repair loop in this milestone.

Implemented M1 CLI behavior: `python -m verilog_copilot verify --rtl <path> --task <fixture_id> --output <run_dir>`. The original acceptance contract below is preserved for regression checks. The registered fixture bundle fixes the checker and its verdict rule.

### Scope and review slices

- M1a: minimal `pyproject.toml`, package entry point, `models.py`, `tools/process.py`, and focused tests. Agree on the VerificationResult/ProcessResult contract first. Use the standard library for runtime code; choose a small test runner and document the command.
- M1b: `tools/simulation.py`, `tools/icarus.py`, minimal `storage.py` and CLI, integration fixtures/tests, `.gitignore`, and a README with executed setup/usage commands. Reuse the runner rather than invoking tools directly from the CLI.
- Create a tiny combinational design/checker, a functional bug, syntax error, and nonterminating simulation fixture. These are synthetic development assets, not modified benchmark material.

Claim exact files before each slice. Package `__init__.py`/`__main__.py` and any new test/config paths must be included in the claim. Do not create unused provider, benchmark, or synthesis skeletons.

### Acceptance checks to execute

1. Correct fixture compiles and simulates with an explicit checker-confirmed pass; artifact paths, commands, versions, hashes, and durations exist.
2. Wrong-behavior fixture compiles and reports functional failure; syntax-error fixture reports compile failure and never runs simulation.
3. Nonterminating simulation hits the configured timeout, terminates its process tree, and records bounded logs and a timeout result.
4. Missing tool is a clear infrastructure error. A process that exits zero without checker completion cannot pass; a candidate's fake pass text cannot override the trusted checker.
5. An existing output directory cannot be silently overwritten; input RTL and checker hashes remain unchanged. Paths containing spaces work without shell interpolation.
6. Unit tests run offline, without SDKs or keys. Real Icarus integration tests run when tools are available; skipped checks are labeled. The handoff lists the exact commands, counts, and results.

Use only team-authored fixtures for M1 execution. If local tool behavior differs from the benchmark's supported environment, document the difference rather than altering the machine globally or claiming benchmark compatibility.

### Handoff to Codex

Provide the exact changed-file list, contract changes, commands/outcomes, sample artifacts, and limitations. Release editing ownership before Codex makes fixes. Codex reviews process handling, oracle integrity, status classification, artifact provenance, and whether the acceptance checks actually ran. The next assignment is M2 only after review of M1's evidence.

## 3. Collaboration and file ownership ledger

Both tools read [PROJECT_SPEC.md](PROJECT_SPEC.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [DECISIONS.md](DECISIONS.md) before work. Shared rules live in PROJECT_SPEC section 5. Human engineering ownership is in [TEAM_ROLES.md](TEAM_ROLES.md).

Before implementation, add a row with a task/slice, editor, exact files, and state. Updating this shared ledger is itself serialized. Proposed globs/directories are not an adequate claim when another editor may be active. Read-only review may overlap; writes may not. If ownership is uncertain, pause affected edits until the assigned editor releases them. Do not ask both tools to implement the same milestone concurrently.

| Task / slice | Active editor | Exact file paths | State / next handoff |
| --- | --- | --- | --- |
| M0 documentation | None | `AGENTS.md`, `CLAUDE.md`, `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/TEAM_ROLES.md`, `docs/DECISIONS.md` | Planning files created; team review pending. No active editing claim after delivery. |
| M1a + M1b (assigned together by the team as "Phase 0") | None (released by Claude Code, 2026-11-08) | `pyproject.toml`, `.gitignore`, `README.md`, `src/verilog_copilot/__init__.py`, `src/verilog_copilot/__main__.py`, `src/verilog_copilot/cli.py`, `src/verilog_copilot/models.py`, `src/verilog_copilot/storage.py`, `src/verilog_copilot/tools/__init__.py`, `src/verilog_copilot/tools/process.py`, `src/verilog_copilot/tools/icarus.py`, `src/verilog_copilot/tools/simulation.py`, `src/verilog_copilot/benchmarks/__init__.py`, `src/verilog_copilot/benchmarks/local_fixtures.py`, `tests/conftest.py`, `tests/unit/test_process.py`, `tests/unit/test_checker_rule.py`, `tests/unit/test_storage.py`, `tests/unit/test_cli.py`, `tests/integration/test_icarus_verify.py`, `tests/integration/test_cli_end_to_end.py`, `tests/fixtures/adder4/tb_adder4.v`, `tests/fixtures/adder4/candidates/{correct,wrong_behavior,syntax_error,hang,early_finish,fake_pass}.v`; this ledger row only in `docs/ROADMAP.md` | Implemented; `pytest`: 54 passed (Icarus 13.0 present), 39 passed + 15 labeled skips without Icarus. Awaiting Codex review; no active editing claim. |
| M1 correction follow-up: CLI SIGTERM/SIGHUP cleanup; bounded screen output | None (released by Claude Code, 2026-11-08) | `src/verilog_copilot/cli.py`, `src/verilog_copilot/rtl.py`, `tests/unit/test_cli.py`, `tests/unit/test_rtl_policy.py`, `README.md`, `docs/DECISIONS.md` (M1-D2 exit codes only), this ledger row | Implemented. Final `pytest`: 130 passed with Icarus 13.0; 100 passed + 30 labeled skips without Icarus. Evidence run for the current source: `runs/adder4-correct-m1-correction-v3/`. The earlier runs `runs/adder4-correct-m1-correction/` and `-final/` are superseded (they predate later source edits) but kept. Awaiting Codex re-review; M2 not started. |
| M1 correction (review findings M1-C1, C2, C3, I1, I2, N1, N2) | None (released by Claude Code, 2026-11-08) | `src/verilog_copilot/models.py`, `src/verilog_copilot/cli.py`, `src/verilog_copilot/rtl.py` (new), `src/verilog_copilot/tools/process.py`, `src/verilog_copilot/tools/simulation.py`, `tests/unit/test_process.py`, `tests/unit/test_cli.py`, `tests/unit/test_rtl_policy.py` (new), `tests/unit/test_simulation_policy.py` (new), `tests/integration/test_icarus_verify.py`, `tests/integration/test_cli_end_to_end.py`, `tests/fixtures/adder4/candidates/{nonce_forgery,hierarchical_tamper,hang_silent}.v` (new), `README.md`, `docs/DECISIONS.md` (status note + proposed entries), `docs/ARCHITECTURE.md` (line-3 status and section 5 generated-RTL gate bullet only), `docs/ROADMAP.md` (this row and M2/M3 gate wording only). Trusted checker `tb_adder4.v` and existing candidate fixtures are not edited. | Implemented; see the follow-up row above for final test counts and the current evidence run. No active editing claim. |
| M1 independent review handoff document | None (released by Codex, 2026-11-08) | `docs/reviews/M1_REVIEW.md`, `docs/ROADMAP.md` (this ownership row only) | Completed: saved the independent review and correction acceptance criteria; implementation unchanged; M1 unapproved pending corrections and re-review. |
| M1 R2 correction (findings M1-C1 lexer/token bypasses, M1-I1 version-probe capture, M1-R2-N1 wording) | None (released by Claude Code, 2026-11-08) | `src/verilog_copilot/rtl.py`, `src/verilog_copilot/models.py`, `src/verilog_copilot/tools/icarus.py`, `src/verilog_copilot/tools/simulation.py`, `tests/unit/test_rtl_policy.py`, `tests/unit/test_simulation_policy.py`, `tests/integration/test_icarus_verify.py`, `tests/integration/test_cli_end_to_end.py`, `README.md`, `docs/DECISIONS.md` (M1-D4 and M1-D6 entries only), `docs/reviews/M1_HANDOFF_R2.md` (new), `docs/reviews/README.md` (implementation-handoff section only), `docs/ROADMAP.md` (this row only). Trusted checker, existing fixtures, historical reports, and existing `runs/` directories are not edited. | Implemented; see [M1_HANDOFF_R2.md](reviews/M1_HANDOFF_R2.md). Final `pytest`: 287 passed with Icarus 13.0; 239 passed + 48 labeled skips without Icarus. Final evidence run `runs/adder4-correct-m1-r2-correction-final/` (manifest hashes match current source); `runs/adder4-correct-m1-r2-correction/` and earlier runs kept but superseded. Awaiting Codex re-review (R3); M2 not started. No active editing claim. |
| Permanent review workflow and M1 R2 report | None (released by Codex, 2026-11-08) | `AGENTS.md`, `CLAUDE.md`, `docs/reviews/M1_REVIEW_R2.md`, `docs/reviews/README.md`, `docs/ROADMAP.md` (this ownership row only) | Completed: saved R2 (CHANGES REQUIRED), aligned 12 permanent workflow rules, and indexed history; original report and application unchanged; no M2 work. |
| M1 independent re-review R3 | None (released by Codex, 2026-11-08) | `docs/reviews/M1_REVIEW_R3.md`, `docs/reviews/README.md`, `docs/ROADMAP.md` (this ownership row only) | Completed: R3 APPROVED WITH NON-BLOCKING ISSUES for trusted-fixture scope; independently executed 287 passed with Icarus and 239 passed / 48 labeled skips without it; C1/I1 verified fixed; two minor follow-ups recorded. Application unchanged; M2 not started. |
| M1 closeout (status docs, decision summary, follow-up backlog, Git preparation) | None (released by Claude Code, 2026-11-08) | `.gitignore`, `.gitattributes` (new), `README.md` (status and limitations only), `docs/ROADMAP.md` (section 1 progress note, new follow-up backlog section, this row), `docs/DECISIONS.md` (current-status note, section 6 pending-confirmation summary, M1-D1/M1-D3 amendments), `docs/ARCHITECTURE.md` (current-status line only). No application code, tests, fixtures, trusted checker, review reports, or `runs/` are edited. No `git init`, commit, remote, or push. | Completed: progress table (section 1), follow-up backlog (section 5), DECISIONS pending-confirmation summary (all M1 entries still proposed), `.gitattributes` `*.v -text` verified by a scratch `core.autocrlf=true` clone (checker hash preserved; 287 passed in that clone). Repository not initialized; ready for the team's first local commit. No M2 work. |
| M2 implementation planning | None (released by Codex, 2026-11-08) | `docs/milestones/M2_PLAN.md`, `docs/ROADMAP.md` (this ownership row only) | Completed: [M2 plan](milestones/M2_PLAN.md) based on committed M1 baseline `7b4fbbe`; contracts, four-role tasks, tests, acceptance gates, security restrictions and pending decisions recorded. Documentation only; application unchanged; M2 not implemented. |

| M1 GitHub publication and current project metadata | None (documentation editing released by Codex, 2026-11-11) | `README.md`, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `docs/PROJECT_SPEC.md`, `docs/TEAM_ROLES.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, `docs/reviews/M1_REVIEW_R4.md`, `docs/reviews/README.md` | Documentation prepared and reviewed; 287 passed with Icarus, 239 passed / 48 skips without it, and 287 passed from a clean export. M1 source/tests and old reports unchanged; local/remote starter histories integrated without force. Git publication/tag execution remains part of the explicitly authorized task and is verified in the final handoff after completion. Existing M2 plan preserved; no M2 implementation. |

The ledger is coordination, not an OS lock. The person starting each session must ensure there is only one active editor for its files. Reclaim stale rows only after confirming the prior editor has stopped; never infer release from elapsed time alone.

## 4. Risks and scope responses

| Risk | Early action | Response if unresolved |
| --- | --- | --- |
| Credentials, model quota, or budget unavailable | Build mock/replay paths in M2; team chooses access and explicit spending budget. | Continue offline engineering; mark live research blocked and make no efficacy claims. |
| Benchmark/simulator incompatibility | Role 3 qualifies reference and bad candidates on a pinned subset before campaigns. | Use a compatible pinned toolchain or select the other allowed suite; document exclusions and protocol changes. |
| Repair overfits feedback checkers | Freeze feedback policy and prompt tuning split; use held-out checks where available. | Label feedback-assisted results and generalization limits. |
| Synthesis library/timing unavailable | Role 3 plans a separately assigned feasibility spike before M5. | Report interim cell-count proxies as proxies; area/timing remains incomplete until a valid flow exists. |
| Too much scope for four students | Keep one CLI, one simulator, one suite, simple adapters. | Defer UI, second suite, FPGA, and optimization extras. |
| Shared interface churn or simultaneous writes | Freeze contracts per slice and use exact-file ownership/handoffs. | Split follow-up tasks; record incompatible changes before integration. |

## 5. Follow-up backlog

These tasks are recorded, not assigned. Each needs a separate assignment and an exact-file claim in section 3. Each also needs an implementation handoff under `docs/reviews/`, and Codex must verify it against the acceptance text below (R3 section 9). If a task is deferred past its "needed before" point, record that disposition explicitly.

| ID | Source | Task | Severity | Needed before | Acceptance (from R3 section 6) | State |
| --- | --- | --- | --- | --- | --- | --- |
| FU-M1-1 | [M1-R3-N1](reviews/M1_REVIEW_R3.md#m1-r3-n1--version-probe-filenames-collide-for-explicit-tools-sharing-a-basename) | Name the version-probe log files by logical tool or stage (compile/simulation), not by executable basename, in `tools/icarus.py` and `tools/simulation.py`. Never overwrite an earlier probe's evidence. Add a regression with two same-basename wrapper tools. | Minor | Relying on wrapper-based or generalized tool configuration (explicit `--iverilog`/`--vvp` paths that share a basename) | Each stage references its own preserved version output even when explicit tool paths share a basename. | Open; unassigned |
| FU-M1-2 | [M1-R3-N2](reviews/M1_REVIEW_R3.md#m1-r3-n2--verdict-documentation-still-equates-policy-rejection-with-functional-defect) | Clarify the `Verdict` docstring in `models.py`. `fail` is a failed verification or admission outcome, and the category gives the reason; a policy rejection is not a functional mismatch. Do not rename enums or change exit codes. | Minor, documentation only | The next result-contract documentation update, and before any evaluation counts `fail` results | Result-model documentation agrees with the adopted policy and distinguishes functional mismatches from unsupported-subset rejections. No runtime change is needed. | Open; unassigned |
