# Independent M1 Re-review — Round 3

Date: **November 8, 2026**  
Milestone: **M1 — Offline Icarus Verification Harness**  
Review round: **R3**  
Reviewer: **Codex — Software Architect and Technical Reviewer**  
Verdict: **APPROVED WITH NON-BLOCKING ISSUES**  
Previous reports: [R1](M1_REVIEW.md), [R2](M1_REVIEW_R2.md)  
Implementation claims reviewed: [M1_HANDOFF_R2.md](M1_HANDOFF_R2.md)

## 1. Technical disposition

M1 is technically approved for its documented **team-authored, restricted RTL subset on the exercised macOS/Python 3.14.6/Icarus 13.0 environment**. The original blocking findings and the R2 CR/version-capture gaps are independently verified fixed within that scope. All six original M1 acceptance areas have executed evidence.

A remaining version-log naming collision for explicitly configured tools with identical basenames is non-blocking for the qualified default `iverilog`/`vvp` setup. A result-enum docstring also needs a small clarification. Neither warrants restructuring the application or withholding approval of the demonstrated M1 path.

This approval is not a security certification, benchmark qualification, adoption of proposed team decisions, permission to execute model-generated RTL, or authorization to begin M2 during this task. No application code, tests, trusted assets, historical reports, or existing run artifacts were modified by this review. Only the R3 report, history index, and current ownership-ledger row were edited. No dependencies were installed, no model calls or benchmark campaign ran, and nothing was pushed to GitHub.

## 2. Scope and changes inspected

The review read the permanent instructions, R2 report, Claude Code's correction handoff, updated implementation and regression tests, README/decision amendments, ownership ledger, and final example artifacts. Against the recorded R2 inventory, implementation/test changes were confined to:

- `src/verilog_copilot/{rtl,models}.py`.
- `src/verilog_copilot/tools/{icarus,simulation}.py`.
- `tests/unit/{test_rtl_policy,test_simulation_policy}.py`.
- `tests/integration/{test_icarus_verify,test_cli_end_to_end}.py`.

The process runner, CLI, storage, fixture registry, and earlier process-cleanup tests remained unchanged from the independently exercised R2 implementation. Their tests were rerun as part of the complete R3 suite. Source line references below describe the reviewed snapshot and may shift after subsequent changes.

## 3. Independently executed verification

Environment: existing `.venv`; macOS; Python **3.14.6**; pytest **9.2.0**; Icarus compiler/runtime **13.0 stable**. Test/cache artifacts were placed under `/private/tmp/capstone-m1-r3-3_3xt23t/`, with `PYTHONDONTWRITEBYTECODE=1` and the pytest cache provider disabled.

### Complete suite with real Icarus

From the project root:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp /private/tmp/capstone-m1-r3-3_3xt23t/with-icarus
```

**Observed: 287 passed in 28.95 seconds; exit code 0; zero skips.** The suite contains 239 unit tests and 48 integration tests. Some parametrized integration tests themselves sweep many byte-level payloads; test count is not a count of independent model samples.

### Suite without Icarus on PATH

```bash
PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp /private/tmp/capstone-m1-r3-3_3xt23t/without-icarus
```

**Observed: 239 passed, 48 explicitly skipped in 3.95 seconds; exit code 0.** Skips identify missing `iverilog` and/or `vvp`; they are not passes.

### Independent failure-probe replays

The reviewer built fresh byte-preserving candidates outside the project and called public `verify()`. For the six forgery cases, the reviewer also called the private unscreened implementation strictly as a review comparison on these controlled fixtures. Every unscreened comparison produced a live false pass, confirming that the public-path rejection was meaningful rather than a result of an inert or uncompilable payload.

| Probe | Independently observed result |
| --- | --- |
| Exact R2 payload with lone CR | Unscreened: pass. Public path: `fail / candidate_policy_violation`; compilation not run. |
| Equivalent payload with CRLF | Same result; copied candidate bytes match the original bytes. |
| Equivalent payload with LF | Same result; copied candidate bytes match the original bytes. |
| Backslash-CRLF string continuation followed by forgery | Unscreened: pass. Public path: policy rejection before compilation. |
| Number-prefixed system calls, including `#0$display` and `#0$finish` | Unscreened: pass. Public path: policy rejection before compilation. |
| Number-prefixed hierarchical write, `#256tb_adder4.errors=0` | Unscreened: pass. Public path: policy rejection before compilation. |
| Injected version-log open failure | `unknown / infrastructure_error`; both execution stages `not_run`; probe capture errors retained. |
| Injected version-log write failure | Same result; no compilation or simulation process created. |
| Declared `MODEL_GENERATED` candidate | `execution_policy_blocked`; output directory remains empty. |

The byte-preserving CR payload is recorded in [R2 section 4](M1_REVIEW_R2.md#4-critical-finding-m1-c1-remains-unresolved). The number-prefix and string-continuation payloads are also represented in the executed integration regressions at [test_icarus_verify.py:229](../../tests/integration/test_icarus_verify.py#L229), [test_icarus_verify.py:246](../../tests/integration/test_icarus_verify.py#L246), and [test_icarus_verify.py:270](../../tests/integration/test_icarus_verify.py#L270).

The existing differential tests execute four templates across 36 separator variants and assert which unscreened payloads really forge a pass under Icarus 13.0. Their expected-live assertions passed. This is stronger than a test that merely checks whether selected strings match a rejection regex.

Claude Code's scratch mutation-test counts in its handoff were **not independently rerun**. They remain implementation-reported evidence. R3 instead independently executed the complete suite and the six live-unscreened/public-rejected comparisons above; it does not claim an exact reconstruction of the historical R2 implementation.

### CLI and provenance checks

```bash
.venv/bin/python -B -m verilog_copilot verify \
  --rtl /Users/ycw/Desktop/Capstone/tests/fixtures/adder4/candidates/correct.v \
  --task adder4 \
  --output /private/tmp/capstone-m1-r3-3_3xt23t/fresh-cli
```

Observed: exit code **0**, a functional pass, schema **3**, and manifest source hashes matching the current implementation. All **12** source hashes in `runs/adder4-correct-m1-r2-correction-final/manifest.json` also match the reviewed source. The original checker and six original candidate files match the R1 hash snapshot; their seven files were not weakened to satisfy tests.

Local evidence includes `with-icarus.txt`, `without-icarus.txt`, `targeted-results.json`, byte-level candidates, and run directories under the temporary root above. Those paths are supplementary and may be cleaned later; the material evidence is retained in this report.

## 4. Closure of earlier issues

| Issue | R3 status | Evidence and scope |
| --- | --- | --- |
| **M1-C1 — False-pass prevention**, including R2 lexer bypass | **Fixed for the reviewed M1 subset and demonstrated vectors** | Exact CR/CRLF/LF forgery, string-continuation and number-prefix probes are live without screening and rejected before compilation through the supported path. See [rtl.py:102](../../src/verilog_copilot/rtl.py#L102), [rtl.py:127](../../src/verilog_copilot/rtl.py#L127), and [rtl.py:144](../../src/verilog_copilot/rtl.py#L144). This is not a proof against every hostile RTL program. |
| **M1-C2 — Compiler signal classification** | **Fixed; retained** | Executed signal-stub regressions return infrastructure/unknown and preserve ordinary compilation failure behavior. See [simulation.py:105](../../src/verilog_copilot/tools/simulation.py#L105). |
| **M1-C3 — Process cleanup** | **Fixed within documented POSIX process-group scope; retained** | Full suite reruns SIGINT, successful-leader/redirected-descendant, timeout, and CLI SIGTERM/SIGHUP regressions. Escaping descendants and SIGKILL to the harness remain outside the guarantee. |
| **M1-I1 — Capture-error propagation**, including R2 version probes | **Fixed for the reported failures** | Independent version-open/write injections return infrastructure/unknown before compilation, with `version_probe.capture_errors` preserved. Compilation/simulation capture tests also pass. See [icarus.py:80](../../src/verilog_copilot/tools/icarus.py#L80) and [simulation.py:239](../../src/verilog_copilot/tools/simulation.py#L239). The separate basename-collision edge case below is not an unrecorded capture failure. |
| **M1-I2 — First generated-RTL execution gate** | **Fixed for declared-origin contract; retained** | Direct MODEL_GENERATED replay is blocked without copied/tool artifacts; required-origin and marker-tool tests pass. Authorship is explicitly caller-declared. |
| **M1-N1 — Stale status documentation** | **Fixed for reported status gap** | Status notes and proposed decision entries distinguish current implementation from the historical planning baseline. They remain team proposals. |
| **M1-N2 — Stale example provenance** | **Fixed with fresh matching evidence** | Final correction example matches all 12 current source hashes; fresh independent CLI run also matches. Earlier examples remain historical. |
| **M1-R2-N1 — Restricted subset versus general synthesizability** | **Fixed in documentation** | [rtl.py:17](../../src/verilog_copilot/rtl.py#L17), README and DECISIONS explicitly acknowledge rejection of legal synthesizable constructs. Broader subset qualification is deferred until benchmark work. |

## 5. Original M1 acceptance criteria

| # | Criterion | R3 assessment |
| --- | --- | --- |
| 1 | Correct fixture passes with explicit checker completion and recorded commands, versions, hashes, durations and artifacts. | **Pass** on the qualified default toolchain, including the separate CLI run and schema-3 probe records. |
| 2 | Wrong behavior compiles then fails; syntax errors do not simulate. | **Pass.** Both real-Icarus outcomes and signal/error distinctions are exercised. |
| 3 | Nontermination times out with bounded logs and process cleanup. | **Pass within documented process-group scope.** `hang_silent` covers the public path; reviewed flooding fixtures cover inner capture/timeout behavior. |
| 4 | Missing tools, incomplete checker execution and forged pass text cannot produce an accepted pass. | **Pass for the supported subset and executed forgery regressions.** Admission screening is required; the unscreened test-only path remains vulnerable by design and is not an application interface. |
| 5 | Refuse overwrite, preserve RTL/checker bytes, and handle paths with spaces literally. | **Pass.** Existing collision/path/integrity tests pass; independent byte-copy/hash checks also agree. |
| 6 | Offline tests work without SDKs/keys and unavailable integration checks are explicitly skipped. | **Pass.** Both complete configurations were independently executed. |

## 6. Non-blocking findings

### M1-R3-N1 — Version-probe filenames collide for explicit tools sharing a basename

**Severity: Minor / non-blocking for the qualified default setup.**  
**Locations:** [icarus.py:70](../../src/verilog_copilot/tools/icarus.py#L70), especially the filenames at lines 75–76; [simulation.py:242](../../src/verilog_copilot/tools/simulation.py#L242).

**Verified reproduction:** the reviewer created two trusted wrapper scripts, `<temporary-root>/compiler/tool` and `<temporary-root>/simulator/tool`. Each prints a distinct role/version on `-V` and otherwise delegates to the real installed compiler/runtime. The correct candidate passes real simulation. However, both probes use `tool.version.stdout.log` and `tool.version.stderr.log` in the same directory. The second probe overwrites the first probe's raw logs.

Observed evidence:

```text
verdict: pass
compile.tool_version: compiler wrapper version 1
contents of compile.version_probe.stdout_path: simulator wrapper version 1
compile and simulation probe stdout paths equal: True
```

**Consequence:** structured metadata and the raw file referenced by the first probe can disagree for a supported explicit-tool configuration. Default tools have distinct basenames (`iverilog`, `vvp`), so this does not undermine the qualified M1 evidence or the fixed capture-error behavior.

**Recommended follow-up:** namespace probe files or subdirectories by logical tool/stage rather than executable basename alone. Do not overwrite an earlier probe's evidence. Add a small regression using two same-basename wrappers.

**Acceptance for closure:** each stage references its own preserved version output even when explicit tool paths have the same basename. This can be addressed in a bounded follow-up before relying on wrapper-based or generalized tool configurations; it does not block restricted M2 planning/mock work.

### M1-R3-N2 — Verdict documentation still equates policy rejection with functional defect

**Severity: Minor / documentation-only.**  
**Location:** [models.py:36](../../src/verilog_copilot/models.py#L36).

**Verified evidence:** the `Verdict` docstring says `fail` means definite evidence of a design defect, while the supported path also returns `fail / candidate_policy_violation` for intentionally excluded, potentially correct RTL. The updated RTL-policy documentation correctly acknowledges the distinction, and the result category preserves it.

**Recommended follow-up:** describe `fail` as a failed verification/admission outcome with the category identifying the reason. Do not rename enums, change exit codes, or count every policy rejection as a measured functional mismatch. Future repair/evaluation must route on category as already planned.

**Acceptance for closure:** result-model documentation agrees with the adopted policy and distinguishes functional mismatches from unsupported-subset rejections. No runtime change or implementation-mirroring test is necessary for a prose clarification.

No new critical or important blocker was verified in R3. The two findings above are practical follow-ups, not grounds for broad refactoring.

## 7. Rulings on deliberate correction choices

| Choice | R3 ruling |
| --- | --- |
| Reject `$` inside identifiers and identifiers ending in forbidden keywords, such as `enforce`. | Acceptable conservative M1 restriction, explicitly documented. It creates intentional exclusions of legal RTL; the team must adopt the tradeoff and revisit it before benchmark evaluation. A complete Verilog lexer is not required to finish this trusted-fixture milestone. |
| Detect number-prefixed hierarchy/system/keyword constructs. | Accept. Independent live-forgery comparisons confirm why the old identifier-boundary exemption was unsafe. |
| Reject multiline/string-continuation and unterminated-string forms. | Accept for the declared subset. Syntax-invalid cases may now fail admission before compilation; the category makes that stage explicit. |
| Reclassify `early_finish`, `fake_pass`, and flooding `hang` as precompile policy violations. | Accept. Inner-layer tests preserve dynamic checker/capture coverage; `hang_silent` covers public-path timeout. |
| Add `StageResult.version_probe` and advance schema to 3. | Accept. The implementation preserves probe commands, statuses, capture failures and paths rather than hiding a failed preflight behind null version strings. |
| Allow a cleanly recorded but unrecognized/nonzero version probe to continue. | Accept for local M1 smoke verification, with explicit raw evidence. This is a portability policy, not successful version qualification. Research campaigns still need known/pinned tools; team confirmation is required. |
| Cap lexical problems and token violations together. | Accept. Flood regressions are executed and keep output within 20 entries plus a truncation marker. This is an entry-count bound, not a claim that all hostile input/resource scenarios are solved. |

## 8. Remaining limitations and team decisions

Verified evidence supports the exercised scope only. The lexical screen is not a parser, synthesis proof, authenticated checker, or OS sandbox. Hostile RTL outside the admitted/trusted scope, another Icarus version's lexer behavior, generated-code isolation, and non-POSIX platforms are not certified by these tests. Descendants leaving the owned process group and SIGKILL to the harness remain documented lifecycle limitations. Compiler diagnostics still require sanitization before future model feedback.

The declared-origin gate must remain closed for model-generated RTL until the isolation policy is adopted and validated. An M2 provider may generate/store text only within its separately assigned scope; it must not relabel generated output as team-authored to execute it. Reviewed mock fixtures remain the offline integration path. No M2 implementation occurred during R3.

Before the first Git commit, the team should explicitly confirm the proposed entries in [DECISIONS.md](../DECISIONS.md), particularly:

1. **M1-D1:** setuptools/src layout, pytest, local `.venv`, and dependency/version recording.
2. **M1-D2:** pass/fail/unknown categories, policy rejection versus mismatch, CLI exit codes, and cancellation semantics.
3. **M1-D3:** trusted fixture location, editable/source-checkout dependency, checker protocol, hash pinning, and a Git line-ending policy preserving pinned `.v` bytes. No `.gitattributes` was added by this review.
4. **M1-D4:** the exact restricted RTL subset and its intentional false positives, with benchmark qualification still required before M4.
5. **M1-D5:** required origin declaration and the gate before first generated-RTL execution; isolation remains a later decision before lifting that gate.
6. **M1-D6:** schema 3, version-probe evidence, unknown/nonzero version-probe policy, and documented contract deviations.

Record actual team adoption; this technical review does not silently promote proposed decisions to confirmed ones. Confirm the tested Python/Icarus environment separately from any future benchmark toolchain. No repository initialization, commit, remote creation, or push is performed or authorized by this report.

## 9. Handoff and future review criteria

There is no blocking M1 correction required by R3. The next work must be separately assigned under the ownership ledger. Address M1-R3-N1 before relying on same-basename wrappers and clarify M1-R3-N2 when updating result-contract documentation. Record explicit disposition if either is deferred.

For any follow-up, Claude Code must read this report, claim exact paths, preserve trusted assets and historical reports, execute the checks relevant to the change, save a unique implementation handoff, and release ownership. Codex should verify the specific closure criteria in section 6 and rerun affected regressions; broaden testing only when the change warrants it. A subsequent formal review must receive a new round/file rather than modifying R3.

**Final technical disposition: APPROVED WITH NON-BLOCKING ISSUES for M1's documented trusted-fixture scope.** Broader execution, major architecture choices, and the next milestone retain their separate team decisions and authorization requirements.
