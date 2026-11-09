# Decisions and Open Questions

Baseline date: November 8, 2026. This record separates supplied requirements and adopted architectural boundaries from proposed implementation choices. “Confirmed” does not imply faculty approval. No implementation or experiment has been completed.

> **Current status (updated November 8, 2026, M1 closeout).** The sentence above describes the planning baseline.
>
> - M1, the offline Icarus verification harness, is **technically approved** by Codex in [reviews/M1_REVIEW_R3.md](reviews/M1_REVIEW_R3.md) (APPROVED WITH NON-BLOCKING ISSUES) for team-authored RTL in the restricted subset on macOS / Python 3.14.6 / Icarus 13.0. Two minor follow-ups are in the ROADMAP follow-up backlog.
> - Technical approval is **not** team adoption. The M1 implementation choices in section 6 remain **proposed** until the team records a decision; see the summary at the start of section 6.
> - No LLM generation, benchmark run, or experiment has been performed. M2 has not started.

For a consequential change, append/update an entry with ID, date, status, owner, context, alternatives, decision, rationale, consequences, and evidence. Preserve superseded decisions with a link to their replacement; do not silently rewrite history. Promote a proposal only after an explicit team decision or an authorized implementation choice with its rationale recorded.

## 1. Confirmed requirements and working boundaries

| ID | Decision / requirement | Basis and consequence |
| --- | --- | --- |
| C01 | Project is “An LLM Copilot for Verilog Design,” Rutgers ECE Group 62, four students; advisor Professor Hang Liu. | Supplied by the team on November 8, 2026. Student names remain unassigned. |
| C02 | Use the existing local `Capstone` root; preserve files; no nested project or GitHub creation/push. | Explicit task constraints. Initial inspection found an empty workspace. |
| C03 | Natural language → RTL → compile/simulate → diagnostics → bounded LLM repair. | Required scope. A compile-only demonstration is insufficient. |
| C04 | Modular Python, interchangeable runtime LLM providers; Icarus or Verilator simulation. | Required scope. Do not assume keys, GPUs, or paid services. |
| C05 | Evaluate on VerilogEval or RTLLM; compare one-shot and repair; report pass@1/pass@k and synthesis area/timing. | Required scope. One selected benchmark is enough; FPGA is optional. |
| C06 | Codex initially plans/reviews/tests; Claude Code initially implements. Either may change role when explicitly assigned. | Supplied collaboration rule. One active editor per file, small reviewable milestones. |
| C07 | Trusted benchmark testbenches/checkers cannot be changed to force passes; tests must be executed before claiming they passed. | Supplied integrity rules; applies to both agents. |
| C08 | Current task creates planning/instruction documents only. | Explicit assignment. No full RTL agent, dependencies, benchmark download, or live model call in M0. |
| C09 | Controller, providers, tools, benchmark adapters, evaluation, synthesis, and artifact storage have distinct contracts. | Architect's baseline adopted in this documentation task, derived from modularity/provider interchangeability. Keeps SDK/tool details out of core policy. Concrete paths/signatures remain adjustable. |
| C10 | Repair lineage is separate from independent sampling; report repair success separately from ordinary pass@k. | Architect's evaluation baseline; dependent attempts cannot be counted as independent generations. See PROJECT_SPEC section 4. |
| C11 | Use explicit verdicts, separate infrastructure/model failures, and preserve raw evidence with provenance. | Architect's correctness/reproducibility baseline. Prevents false passes and misleading aggregate results. |
| C12 | Offline mock/replay operation is required for development; secrets are excluded from tool environments and artifacts. | Architect's baseline enabling progress without assumed credentials or hardware. |

## 2. Proposals awaiting implementation choice or team review

| ID | Proposal | Rationale / alternative / gate |
| --- | --- | --- |
| P01 | Start with a synchronous CLI and standard-library runtime modules. | Smallest useful interface; GUI/web service can be reconsidered after core evaluation. Choose packaging/test tools during M1. |
| P02 | First simulator adapter: Icarus (`iverilog` + `vvp`). | Already installed; alternative is Verilator with a compatible execution harness. Pin versions only after benchmark qualification. |
| P03 | Begin with VerilogEval's specification-to-RTL task and a fixed development subset. | Matches natural-language scope. Alternative: RTLLM after a portability spike. No benchmark version or subset is selected yet. |
| P04 | Use the proposed `src/verilog_copilot/` layout and JSON artifacts/CSV summaries. | Keeps boundaries visible with minimal infrastructure; final package/tool settings are chosen in M1. No database proposed. |
| P05 | Prefer synthesizable Verilog-2005 RTL, with explicitly declared benchmark-required SystemVerilog features. | Reduce language complexity without changing benchmark semantics. Final supported feature subset depends on tool/task qualification. |
| P06 | Yosys mapping plus OpenSTA timing using an accessible Liberty library and explicit SDC constraints. | Open-source candidate flow; library/corner, tool versions, units, and constraints must be proven in an early spike. Alternative flow needs equivalent reproducible evidence. |
| P07 | First passing candidate per trajectory for area/timing; paired one-shot/repair initial candidates; independent resampling control. | Limits selection bias and separates feedback benefit from extra budget. Final protocol is frozen before campaigns. |
| P08 | M1 is an offline simulator harness with known-good/bad/hanging fixtures. | Establish trustworthy verification before LLM integration. Assignment and acceptance contract are in ROADMAP. |

## 3. Unresolved questions and when to resolve them

Owners refer to proposed engineering roles; named students are not assigned yet.

| ID | Question | Owner / decision gate |
| --- | --- | --- |
| Q01 | Which student takes each role, and what are actual availability and course/advisor milestones? | Team / before scheduling implementation. Estimates are not deadlines. |
| Q02 | Which runtime providers/models are accessible, with what budget, quota, data policy, and supported sampling controls? | Role 2 + team / before live M2 calls. Development subscriptions do not establish runtime API access. |
| Q03 | Which benchmark, revision, task format, supported subset, and license/use constraints apply? | Roles 3/4 / before M4; record provenance before import. |
| Q04 | Which Python/simulator versions and local or isolated environment support the chosen benchmark? Does the installed Icarus v13 pass qualification, or should benchmark runs use v12? | Roles 1/3 / compatibility spike before M4. Do not downgrade globally without an explicit implementation decision. |
| Q05 | What isolation mechanism can restrict generated-code execution on team machines without assuming Docker? | Roles 1/3 / before arbitrary generated RTL execution in M3. M1 stays on team-authored fixtures. |
| Q06 | What are the repair, request/token/time, retry, feedback-size, log, and artifact limits? Which failures are retryable? | Roles 1/2/3 / M2/M3; all campaign limits explicit in manifest. |
| Q07 | What `n`/`k`, task split, repeats, sampling settings, outage policy, and cost-matched comparison fit resources? | Role 4 + team / freeze before M6. No arbitrary numerical pass target is assumed. |
| Q08 | Which feedback is exposed, and are independent held-out checkers available? | Roles 2/3/4 / before M3 benchmark repair. Label feedback-assisted results even if held-out checks are unavailable. |
| Q09 | Which library/corner, synthesis/STA versions, clock/I/O constraints, units, and timing-coverage rules are usable? | Role 4 / feasibility spike during M2; resolve before M5. Generic counts do not close the area/timing requirement. |
| Q10 | What evidence and numerical goals does the team/advisor expect for final success? | Team / early scope discussion; record actual instructions only. |
| Q11 | Is FPGA work useful and feasible; which board/tool access exists? | Team / after core results; optional and currently unplanned. |

## 4. Observed local environment

Read-only inspection on November 8, 2026 found Python **3.14.6**, Icarus Verilog **13.0 stable**, and `vvp` on PATH. `verilator`, `yosys`, and `sta` were not found on PATH; this does not prove they are absent elsewhere. No compiler/simulation test or model call was executed during planning. No credentials were inspected.

The [VerilogEval README](https://github.com/NVlabs/verilog-eval/blob/main/README.md) describes Python 3.11.0/Icarus v12 and cautions against its v13 development setup. Our installed v13 identifies as stable, but compatibility is **unverified**. This observation is not a toolchain decision. [RTLLM](https://github.com/hkust-zhiyao/RTLLM/blob/main/README.md) includes VCS-oriented execution instructions, so open-source simulator portability is also unverified. These source notes were checked November 8, 2026; pin exact revisions during benchmark selection.

## 5. Decision-entry template

```text
ID and title:
Date:
Status: proposed | confirmed | superseded
Owner and decision authority:
Context / requirement IDs:
Options considered:
Decision and rationale:
Consequences / affected contracts and files:
Validation or evidence (executed vs planned):
Replaces / follow-up questions:
```

## 6. M1 implementation choices (proposed, pending team confirmation)

These entries record choices that M1 implemented and that Codex reviewed in [reviews/M1_REVIEW.md](reviews/M1_REVIEW.md) section 8. "Implemented" does not mean confirmed. Each entry stays **proposed** until the team decides.

### Pending team confirmation (summary prepared at M1 closeout, November 8, 2026)

Reviewer rulings are cited per row from [R1](reviews/M1_REVIEW.md) section 8 and [R3](reviews/M1_REVIEW_R3.md) sections 4 and 7. R3 section 8 asks the team to confirm all six entries. A ruling of "accept" is a reviewer recommendation, **not** team adoption. To adopt an entry, record the date, who decided, and the outcome below, then change that entry's `Status:` to `confirmed`, or to `superseded` with a link. Nothing here has been confirmed.

| Entry | What the team is asked to confirm | Reviewer ruling (source) | Team decision |
| --- | --- | --- | --- |
| M1-D1 | setuptools src layout; pytest only dev dependency; stdlib-only runtime; project-local `.venv`; `runs/` and local agent/OS files not version-controlled | Accept (R1 §8) | Pending |
| M1-D2 | `pass`/`fail`/`unknown` with categories; a policy rejection is `fail` but a different category from `test_mismatch`; exit codes 0/1/2/3 and 128+signal; no verdict on cancellation | Accept (R1 §8); signal classification verified fixed (R3 §4, C2) | Pending |
| M1-D3 | Trusted checkers in `tests/fixtures/`, sha256-pinned; checkout or editable install required; nonce plusarg and single result-line protocol; `*.v -text` Git line-ending policy | Fixtures: accept for M1 (R1 §8); nonce protocol: modify, addressed by M1-D4. R3 §8 asks for a line-ending policy that preserves pinned `.v` bytes; the `.gitattributes` file was added at closeout, after R3, and has not been reviewed | Pending |
| M1-D4 | Restricted RTL subset and its intentional false positives: `$` inside identifiers, identifiers ending in `force`/`release`/`defparam`, generate-scope references, `` `default_nettype ``, multi-line strings. Must be requalified against the chosen benchmark before M4 | Acceptable conservative M1 restriction; the team must adopt the tradeoff (R3 §7) | Pending |
| M1-D5 | Required `origin` argument; model-generated RTL blocked until an isolation policy (Q05) is adopted and validated; M2 mocks limited to reviewed team fixtures | Fixed for the declared-origin contract (R3 §4, I2) | Pending |
| M1-D6 | Schema "3" with `version_probe`; an unrecognized or non-zero version probe is recorded but not blocking (a portability policy, not version qualification); documented ARCHITECTURE §3 deviations | Deviations: modify slightly (R1 §8). Schema 3 and probe policy: accept; campaigns still need pinned, known tools (R3 §7) | Pending |

Related open questions that gate upcoming work (section 3): Q01 (role assignment), Q02 (provider access before live M2 calls), Q05 (isolation before any model-generated RTL executes), Q06 (repair/retry limits and which `unknown` categories are repairable), and Q04 (benchmark toolchain, kept separate from the tested M1 environment).

```text
ID and title: M1-D1 Packaging and test tooling
Date: 2026-11-08
Status: proposed (implemented; review section 8 recommends "accept")
Owner and decision authority: Role 1 / team
Context / requirement IDs: P01, R8
Options considered: setuptools + pytest + project-local .venv; Poetry/uv/tox (more infrastructure)
Decision and rationale: setuptools (src layout); pytest as the only dev dependency; runtime uses
  the standard library only. Smallest conventional setup.
Consequences / affected contracts and files: pyproject.toml, README.md; `pip install -e '.[dev]'`
  needs network access once.
Validation or evidence (executed vs planned): executed on macOS, Python 3.14.6, pytest 9.2.0.
  Other Python versions/platforms not exercised.
Replaces / follow-up questions: Q04 (toolchain pinning) remains open.
Amendment (2026-11-08, M1 closeout; still proposed): `.gitignore` keeps generated `runs/`, `.venv/`,
  caches, egg-info, `.DS_Store` and `.claude/settings.local.json` out of version control. Run
  evidence is therefore local only; review reports record the material evidence.
```

```text
ID and title: M1-D2 Verdict policy, failure categories and CLI exit codes
Date: 2026-11-08
Status: proposed (review: "accept"; signal mapping corrected per M1-C2)
Owner and decision authority: Roles 1/3 / team
Context / requirement IDs: R3, C11, PROJECT_SPEC section 4
Decision and rationale: verdict `fail` only for definite design defects:
  - candidate_policy_violation
  - compile_error (non-zero compiler exit)
  - test_mismatch (trusted checker reported errors)
  Everything else that is not a pass is `unknown`:
  - compile/simulation timeout
  - checker_inconclusive
  - simulation_error
  - missing_tool
  - infrastructure_error, including tools killed by a signal and log-capture failures
  - execution_policy_blocked
  CLI exit codes: 0 pass, 1 fail, 2 usage, 3 unknown, 128+signal when interrupted
  (130 SIGINT, 143 SIGTERM, 129 SIGHUP; no verdict written, child process groups killed).
Consequences: M3 repair routing must use failure_category, not only verdict.
  For example, simulation_timeout and missing_tool must not be treated alike.
Validation: unit + integration tests in tests/; review probes rerun after the correction.
Follow-up: the team decides which `unknown` categories are repairable (Q06).
```

```text
ID and title: M1-D3 Trusted fixtures and checker protocol
Date: 2026-11-08
Status: proposed (review: fixtures "accept for M1"; nonce protocol "modify" -> see M1-D4)
Owner and decision authority: Role 3 / team
Decision and rationale:
  - Trusted checkers live in tests/fixtures/ and are pinned by sha256 in
    src/verilog_copilot/benchmarks/local_fixtures.py.
  - The pinned hash is verified before and after every run.
  - The checker echoes a per-run nonce passed as a plusarg.
  - Pass requires exactly one well-formed result line with the expected check count and zero errors.
Consequences: needs a source checkout or editable install. A future git repo should mark *.v as
  `-text` (or eol=lf), or the pinned hash breaks on CRLF checkouts.
Validation: tests/unit/test_checker_rule.py; tests/unit/test_storage.py (hash pin).
Amendment (2026-11-08, M1 closeout; still proposed): `.gitattributes` now contains `*.v -text`.
  Executed check in a scratch copy: with `core.autocrlf=true` and no attribute, a clone changed the
  checker's sha256 to ff1885017e63…, breaking the pin. With the attribute, the clone kept 0436fdfb2619…
  while README.md was converted to CRLF, and the full suite passed in that clone (287 passed).
```

```text
ID and title: M1-D4 RTL admission screen (checker-interference restrictions)
Date: 2026-11-08
Status: proposed (implemented in response to review finding M1-C1)
Owner and decision authority: Roles 2/3 / team
Context / requirement IDs: M1-C1, PROJECT_SPEC section 3 (testbench-only constructs are not valid
  designs), section 4 (oracle integrity)
Options considered:
  (a) nonce only: defeated by the review's nonce-aware probe;
  (b) allowlist of candidate hashes: blocks legitimate team RTL;
  (c) lexical screen of the compiled copy (chosen);
  (d) separate-process checker: not possible with a shared simulator.
Decision and rationale: before compilation, reject the following in the private candidate copy:
  - system tasks/functions except $signed, $unsigned, $clog2;
  - hierarchical references;
  - escaped identifiers;
  - force, release, defparam;
  - every compiler directive except `timescale.
  A violation is fail / candidate_policy_violation, and the candidate is not compiled.
Consequences: fake_pass.v, early_finish.v and hang.v are now rejected on the supported path.
  Their former checker-layer classifications are still tested on the inner layer, with the screen
  skipped through a private, test-only entry point. The screen is NOT a sandbox and is not
  proven complete.
Validation or evidence: new evidence beyond the review. A candidate with no system tasks forged
  "checks=256 errors=0" under Icarus 13.0 via `always @(tb_adder4.checks) tb_adder4.errors = 0;`
  (fixture hierarchical_tamper.v). Both that and the review's nonce probe are now rejected
  (tests/integration/test_icarus_verify.py, tests/unit/test_rtl_policy.py).
Follow-up: re-evaluate the screen against the chosen benchmark's legal RTL subset before M4.
Amendment (2026-11-08, M1 R2 correction; still proposed): review M1_REVIEW_R2 found that a lone CR
  ends a // comment in Icarus 13.0 but not in the screen (false pass). The correction also found
  two more bypasses, each verified to forge a pass through public verify() on the R2-era screen:
  - backslash + CRLF inside a string (Icarus continues the string; the screen ended it at LF);
  - a number directly before a construct (`#0$display`, `#256tb_adder4.errors = 0`).
  Rules added:
  - a // comment ends at LF or CR, matching Icarus; VT, FF, NEL and U+2028/2029 do not end it;
  - a string literal must close on its own line. Raw CR/LF or backslash + CR/LF inside a
    string is rejected, not emulated;
  - '$' is allowed only to begin $signed/$unsigned/$clog2, and never directly after an
    identifier character or digit. This deliberately rejects '$' inside identifiers (legal
    Verilog that R2 had seen admitted);
  - force/release/defparam match without an identifier-boundary exemption. This also rejects
    identifiers that end in those words, e.g. `enforce`;
  - a dotted name preceded by a digit is a hierarchical reference.
  Scope wording (M1-R2-N1): these rules define a restricted supported subset for M1. Several
  rejected constructs are legal, synthesizable Verilog (local generate-scope references,
  `default_nettype`, '$' in identifiers); a policy rejection is not a functional mismatch.
  Evidence: docs/reviews/M1_HANDOFF_R2.md.
```

```text
ID and title: M1-D5 Execution gate for model-generated RTL
Date: 2026-11-08
Status: proposed (implements review recommendation M1-I2 and the team's instruction to keep
  generated-RTL execution blocked)
Owner and decision authority: Roles 1/3 / team
Decision and rationale:
  - verify() takes a required keyword `origin` (no default).
  - CandidateOrigin.MODEL_GENERATED returns unknown / execution_policy_blocked before anything is
    copied or run.
  - The gate applies before the FIRST execution of model-generated RTL, regardless of milestone name.
  - M2 mock responses may only be reviewed team fixtures.
Consequences: an API tripwire, not proof of authorship; a caller can still declare
  TEAM_AUTHORED. Lifting the gate requires an adopted and validated isolation policy (Q05).
  Host isolation and same-simulator interference (M1-D4) are separate concerns.
Validation: tests/unit/test_simulation_policy.py.
```

```text
ID and title: M1-D6 Result schema version 2 (now 3) and documented contract deviations
Date: 2026-11-08
Status: proposed (review: "modify slightly")
Decision and rationale:
  Schema "2" adds:
  - ProcessResult.capture_errors
  - VerificationResult.candidate_origin, rtl_screen, policy_violations
  - categories candidate_policy_violation and execution_policy_blocked
  Deviations from ARCHITECTURE section 3, all accepted for M1 by the review:
  - verify() takes explicit (candidate, bundle, limits, run_dir, tools, *, origin)
  - tool version lives on StageResult
  - candidates are identified by path + sha256 (no Candidate/lineage IDs yet)
  - flat per-run artifact layout
Consequences: lineage IDs are needed when generation is integrated (M2).
Amendment (2026-11-08, M1 R2 correction; still proposed): schema "3" adds
  StageResult.version_probe (the `-V` probe's ProcessResult). A version probe with a spawn,
  capture, timeout, signal, or log-read failure stops the run before compilation as
  unknown / infrastructure_error (review M1-I1). A cleanly recorded probe with no recognizable
  version line, or a non-zero probe exit, is recorded but does not block the run.
```
