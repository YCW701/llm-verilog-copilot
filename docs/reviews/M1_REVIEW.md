# Independent Code Review — Milestone M1

Project: **An LLM Copilot for Verilog Design**  
Rutgers ECE Capstone, Group 62 — four undergraduate ECE students  
Faculty advisor: Professor Hang Liu  
Reviewer: Codex, Software Architect and Technical Reviewer  
Review date: November 8, 2026  
Disposition: **M1 is not ready for approval; address the critical findings before M2.**

## 1. Purpose, scope, and handoff rules

This document preserves the latest independent review of Claude Code's M1 offline Icarus verification harness. It is the handoff for a small M1 correction milestone, not permission to start M2 or redesign the application. Recommendations below are reviewer recommendations, not confirmed team or faculty decisions.

The review covered:

- Root [AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md).
- [PROJECT_SPEC.md](../PROJECT_SPEC.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [ROADMAP.md](../ROADMAP.md), [DECISIONS.md](../DECISIONS.md), and [TEAM_ROLES.md](../TEAM_ROLES.md).
- [pyproject.toml](../../pyproject.toml), [README.md](../../README.md), `src/verilog_copilot/`, `tests/`, `tests/fixtures/adder4/`, and `runs/adder4-correct/`.

The implementation is reasonably small and modular, and the reported 54 passing tests are reproducible. Targeted probes nevertheless exposed false-pass, failure-classification, and process-cleanup gaps. Passing the existing suite does not close those gaps.

The independent review changed no project files, installed no dependencies, pushed nothing, and started no M2 work. Review-generated fixtures and artifacts were placed under `/private/tmp`. A final hash/inventory comparison confirmed all 47 reviewed project files, including existing run artifacts, were unchanged.

Saving this handoff adds this document and a coordination row in the roadmap ownership ledger only. It does not change implementation, trusted checkers, existing decisions, architecture, or acceptance criteria. Test results below belong to the independent review session; they were not rerun merely to save this document.

Before making corrections, Claude Code must obtain the relevant assignment, claim exact file paths in the roadmap ledger, and ensure no other agent is editing them. Preserve unrelated changes and trusted verification assets. At completion, provide executed validation and release ownership before reviewer fixes. Do not introduce frameworks, broad refactoring, provider integration, or a repair loop as part of the M1 correction.

## 2. Independently executed verification

Environment observed during the review: macOS, Python **3.14.6**, pytest **9.2.0**, and Icarus Verilog/runtime **13.0 stable**. The existing local `.venv` was used; no dependency installation or live model call was needed.

### Full suite with Icarus available

The review wrapper set `PYTHONDONTWRITEBYTECODE=1` and executed:

```bash
.venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp /private/tmp/capstone-m1-review-je6hcgwm/pytest
```

Observed result: **54 passed in 7.53 seconds**, exit code 0, zero skips. This comprised 39 unit tests and 15 real-Icarus integration tests.

### Suite with Icarus unavailable through PATH

```bash
PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp /private/tmp/capstone-m1-review-je6hcgwm/no-tools-pytest
```

Observed result: **39 passed, 15 skipped in 1.84 seconds**, exit code 0. Skip messages explicitly identified missing `iverilog` and/or `vvp`; skips were not reported as passes. This confirms both previously reported test configurations.

### Independent public CLI run

```bash
.venv/bin/python -B -m verilog_copilot verify \
  --rtl /Users/ycw/Desktop/Capstone/tests/fixtures/adder4/candidates/correct.v \
  --task adder4 \
  --output /private/tmp/capstone-m1-review-je6hcgwm/independent-cli-correct
```

Observed result: exit code **0**, compile and simulation statuses `ok`, verdict `pass`, category `none`, and **256/256 vectors with zero errors**. Fresh JSON artifacts were inspected.

### Targeted probes beyond the supplied suite

| Probe | Observed result | Finding |
| --- | --- | --- |
| Wrong DUT reads nonce, prints a matching result, and finishes at time zero | `pass / none`; claimed 256 checks despite early termination | M1-C1 |
| Compiler stub terminates itself with SIGTERM | `fail / compile_error`, signal 15 | M1-C2 |
| SIGINT interrupts the process runner | Child remained alive after interruption | M1-C3 |
| Successful leader leaves a sleeping descendant with redirected streams | Runner returned exit 0 while descendant remained alive | M1-C3 |
| Stderr log destination is a directory | Pump thread raised `IsADirectoryError`; returned result reported no capture error | M1-I1 |
| Compare saved example's source hashes with current files | `cli.py` differs; candidate and checker hashes match | M1-N2 |

The reviewer explicitly terminated the surviving review-created processes. Local evidence included `pytest-output.txt`, `targeted-results.json`, temporary candidates/tools, and fresh run directories under `/private/tmp/capstone-m1-review-je6hcgwm/`. Temporary paths are not permanent repository artifacts; this document records the material results and reproduction details so the handoff does not depend on their retention.

## 3. M1 acceptance criteria assessment

The six criteria are preserved from ROADMAP section 2; the assessment does not redefine them.

| # | Acceptance criterion | Independent assessment |
| --- | --- | --- |
| 1 | Correct fixture compiles/simulates with explicit checker-confirmed pass; paths, commands, versions, hashes, and durations exist. | **Pass.** Existing integration checks and the separate public CLI run confirm the supplied correct fixture and evidence. |
| 2 | Wrong behavior compiles and fails functionally; syntax error fails compilation and never simulates. | **Pass for supplied fixtures.** Broader compiler-failure classification is incorrect for signal termination; see M1-C2. |
| 3 | Nonterminating simulation times out, its process tree is terminated, and logs are bounded. | **Partial.** Supplied hang/timeout checks pass, including bounded output. Cancellation and normal-exit descendant cleanup are incomplete; see M1-C3. |
| 4 | Missing tool is infrastructure failure; zero exit without checker completion cannot pass; fake candidate pass text cannot override the checker. | **Partial.** Missing tools, plain banners, and ordinary early finish are handled. Nonce-aware forgery produces a false pass; see M1-C1. |
| 5 | Existing output is not overwritten; RTL/checker hashes remain unchanged; paths containing spaces work literally. | **Pass in executed checks.** Collision refusal, literal path handling, and unchanged source/checker evidence were verified. |
| 6 | Unit tests are offline; real-Icarus tests execute when available; skips and actual commands/results are reported. | **Pass.** Both test configurations were independently reproduced. |

## 4. Critical findings — must fix before M2

### M1-C1 — A wrong candidate can forge a checker-confirmed pass

**Locations:** [tools/simulation.py:183](../../src/verilog_copilot/tools/simulation.py#L183), [benchmarks/local_fixtures.py:63](../../src/verilog_copilot/benchmarks/local_fixtures.py#L63). The acknowledged limitation is also in [README.md:113](../../README.md#L113).

**Evidence:** the reviewer created the following temporary candidate without changing the trusted checker:

```verilog
module adder4(input [3:0] a, input [3:0] b, output [4:0] sum);
  assign sum = 0;
  reg [511:0] n;
  initial begin
    if ($value$plusargs("checker_nonce=%s", n))
      $display("CHECKER_RESULT nonce=%0s checks=256 errors=0", n);
    $finish;
  end
endmodule
```

Calling the current `verify` function with this candidate and the registered `adder4` bundle returned `pass / none` and `checker confirmed 256/256 vectors with 0 errors`. The simulator log showed `$finish` at time zero. The DUT is functionally wrong and the trusted checker had not completed its checks. Its source hash remained intact.

**Consequence:** nonce matching does not prove the checker emitted the result. This can falsely label invalid RTL as correct and undermines acceptance criterion 4. It is an acknowledged limitation, but it remains a gap in the broad acceptance claim.

**Recommended fix:** make M1's trusted-candidate restriction enforceable rather than relying only on prose, and add this regression expecting a non-pass result. Before admitting model-generated candidates, define validation and checker-interference restrictions. Keep hostile RTL outside the stated guarantees. A nonce, a source hash, or OS isolation alone cannot authenticate which module printed simulator output. Do not present a simple construct filter as a complete security sandbox.

**Re-review acceptance:** the exact probe above cannot pass through the supported execution path; existing good/bad/early-finish fixtures retain their intended classifications; the admitted candidate scope and remaining oracle limitations are explicit and enforced.

### M1-C2 — Compiler signal termination is classified as a design defect

**Location:** [tools/simulation.py:172](../../src/verilog_copilot/tools/simulation.py#L172).

**Evidence:** an executable review compiler stub printed a version for `-V` and otherwise terminated itself with SIGTERM. Verifying the correct adder with that compiler returned `fail / compile_error`; the process record contained signal **15**. The ordinary `proc.exit_code != 0` branch also matches a signaled process whose exit code is `None`.

**Consequence:** external termination or a compiler crash is attributed to candidate RTL. Future repair may attempt to fix infrastructure failures, and evaluation may count them as definite model defects.

**Recommended fix:** handle `proc.signal` before ordinary nonzero compiler exits. Return verdict `unknown` with an infrastructure/tool-error classification for signal termination. Preserve `fail / compile_error` for actual compilation diagnostics. Keep the signal and raw logs in the evidence.

**Re-review acceptance:** a SIGTERM compiler stub yields `unknown` and an appropriate infrastructure/tool-error category; the syntax-error fixture still yields `fail / compile_error` with simulation `not_run`; add focused regression coverage.

### M1-C3 — Process cleanup is not guaranteed on all runner exits

**Locations:** [tools/process.py:139](../../src/verilog_copilot/tools/process.py#L139), [tools/process.py:148](../../src/verilog_copilot/tools/process.py#L148).

**Evidence:** two independent probes reproduced surviving processes:

1. Start a sleeping child through `run_process`, interrupt the review runner with SIGINT, catch `KeyboardInterrupt`, and inspect the child PID. The child remained alive.
2. Start a leader that launches a sleeping descendant with stdin/stdout/stderr redirected to `DEVNULL`, writes its PID, and exits successfully. `run_process` returned exit 0 while the descendant remained alive. Redirecting streams avoids the existing pump-alive cleanup condition.

**Consequence:** cancellation or a successful leader exit can leave tool descendants running beyond the harness's intended lifecycle. Repeated runs can leak processes and resources even though the supplied timeout test passes.

**Recommended fix:** make cleanup exception-safe for owned processes, pipes, and threads. Cover cancellation and remaining owned descendants after leader exit, not only `TimeoutExpired` or open output pipes. Reap the leader and close/join capture resources. Keep the solution scoped to the existing POSIX process-group approach; do not add a process-management framework.

**Re-review acceptance:** neither probe leaves a live review-owned process after cleanup; the existing timeout/process-tree test still passes; cancellation remains distinguishable from a design failure; logs and resource cleanup remain bounded. Add both regressions and clean up their children even if an assertion fails.

## 5. Important findings — should fix soon

### M1-I1 — Log-capture failures are lost inside worker threads

**Locations:** [tools/process.py:54](../../src/verilog_copilot/tools/process.py#L54), [tools/process.py:158](../../src/verilog_copilot/tools/process.py#L158).

**Evidence:** using a directory as the stderr log destination raised `IsADirectoryError` in `_BoundedPump`. The returned process record nevertheless contained `exit_code=0`, `spawn_error=null`, `stderr_bytes=0`, and `stderr_truncated=false`, with no capture-error indication. The stderr path was still a directory.

**Consequence:** failed log creation or writes can discard diagnostic evidence without a structured infrastructure failure. A process exit code alone does not establish that evidence capture succeeded.

**Recommended fix:** propagate pump/open/write failures into the process result and make verification infrastructure/unknown when required evidence capture fails. Ensure process and pipe cleanup still occurs. Document/schema-version any incompatible record change.

**Re-review acceptance:** log-open and simulated log-write failures are observable in structured results, cannot produce a functional pass, and leave no live child or capture thread. Add focused tests for both cases; retain stdout/stderr truncation behavior.

### M1-I2 — The isolation gate follows M2's first proposed generated-code execution

**Locations:** [ROADMAP.md:11](../ROADMAP.md#L11), [README.md:112](../../README.md#L112).

**Evidence:** M2 includes a generation-to-verification path, while the stated gate defers isolation until M3. The README correctly says the current harness is not a sandbox and only team-authored fixtures should execute.

**Consequence:** following milestone names literally could execute model-generated RTL before the intended execution-policy gate. Minimal environments, timeouts, and working directories do not restrict filesystem/network access or provide complete resource isolation.

**Recommended fix:** make the gate apply before the **first execution of model-generated RTL**, regardless of milestone name. M2 mock responses may remain reviewed fixtures. Full isolation infrastructure is unnecessary for the present trusted-fixture demonstration. Treat host isolation and same-simulator oracle interference as separate concerns.

**Re-review acceptance:** documentation and the supported execution path agree on the trusted-fixture boundary; broader execution remains gated until the chosen policy is documented and validated. Do not assume Docker or other infrastructure is available.

## 6. Minor findings — can be addressed later

### M1-N1 — Architecture and decision-record status are stale

**Locations:** [DECISIONS.md:3](../DECISIONS.md#L3), [ARCHITECTURE.md:3](../ARCHITECTURE.md#L3).

**Evidence:** the decision record still states no implementation has been completed; the architecture introduction states no application modules exist. M1 now implements several contracts, and its tooling/verdict choices are described outside the decision record.

**Consequence:** teammates and development agents can confuse historical planning status with current behavior or treat undocumented choices as approved decisions.

**Recommended fix:** preserve the historical planning baseline while identifying current implementation status. Record M1 tooling, interfaces, verdict policy, limitations, and their actual review/decision status. Do not promote these review recommendations to confirmed decisions without the appropriate decision authority.

**Acceptance:** current state and historical baseline are distinguishable; important interface choices and limitations have traceable decision entries.

### M1-N2 — The saved example predates the current CLI source

**Location:** [runs/adder4-correct/manifest.json](../../runs/adder4-correct/manifest.json), field `code_sha256["cli.py"]`.

**Evidence:** the saved CLI hash is `8474110bdc0c531db5566aeb3e379db7bc5d30348266c8d8b8536d335eeabd14`; the reviewed current CLI hash is `23953e5ce206f4333637ee3f8ec73d9175b66b379e4b1bdc93d373f49780ecf3`. Candidate and checker hashes match their current files. The reviewer separately executed the current CLI successfully.

**Consequence:** the saved example is identifiable historical evidence, not execution evidence for the exact current CLI revision. This does not invalidate the fresh independent run.

**Recommended fix:** after corrections, create an example in a new run directory and verify its source, candidate, and checker hashes. Preserve the existing run rather than overwrite it.

**Acceptance:** a fresh example manifest matches the corrected source and is identified as the evidence for that revision.

## 7. Architecture compatibility and maintainability

The main boundaries are sound: subprocess execution is centralized, Icarus flags are isolated, checker interpretation belongs to the fixture adapter, and the CLI remains small. Standard-library runtime code and atomic, collision-refusing JSON publication are appropriate. The findings do not justify rewriting the module structure.

| Implemented difference from ARCHITECTURE | Assessment and next step |
| --- | --- |
| `verify(candidate, bundle, limits, run_dir, tools)` adds explicit dependencies. | Reasonable M1 implementation detail; document the concrete signature. |
| `simulation.py` directly depends on `IcarusTools`. | Acceptable for one backend. Introduce a neutral boundary when another backend actually arrives. |
| Tool version is in `StageResult`, outside `ProcessResult`. | Acceptable distribution of metadata; document it. |
| Candidate identity uses path/hash instead of a `Candidate` record. | Sufficient for M1. Add candidate/sample/attempt/parent IDs when generation is integrated. A content hash is not a unique attempt ID. |
| `TaskSpec`, approved public feedback records, and trajectory hierarchy are absent. | Appropriate deferral; keep private verification bundles out of future provider-visible records. |
| Each run has a flat artifact layout. | Appropriate M1 simplification; later nest these records under experiment/sample/attempt directories without rewriting verification. |

Future repair routing must use failure category as well as verdict. `unknown/simulation_timeout` and `unknown/missing_tool` must not automatically receive the same treatment. Compiler diagnostics containing trusted source must be sanitized before feedback; raw local evidence should remain available. No provider or repair implementation is requested in this handoff.

## 8. Recommended technical decisions

These are review recommendations. Record any adopted choices in DECISIONS through the existing project process.

| Decision | Classification | Reason / condition |
| --- | --- | --- |
| Setuptools, pytest, local `.venv`. | **Accept** | Small, conventional setup; the existing environment works. |
| Trusted checkers under `tests/fixtures`. | **Accept for M1** | Source-checkout dependency is explicit. Defer packaged fixture support until needed. |
| Nonce-based pass/fail protocol. | **Modify** | Useful against naive banners; insufficient against nonce-aware candidates. See M1-C1. |
| CLI exit codes 0/1/2/3. | **Accept** | Clearly distinguish pass, failure, usage error, and unknown. Correct signal mapping under M1-C2. |
| Conservative unknown verdict policy. | **Accept** | Avoids correctness claims without evidence; retain meaningful failure categories. |
| Result models and verification metadata. | **Modify slightly** | Preserve the structure; add capture-error evidence and document interface deviations. |
| Candidate identity by path/hash. | **Accept for M1** | Add lineage IDs at generation integration; hashes identify content, not separate attempts. |
| Current simulation isolation limitations. | **Accept only for trusted M1 fixtures** | Enforce the restriction; broader execution policy must precede generated RTL execution. |
| Python 3.14 / Icarus 13 locally. | **Accept for M1** | Independently exercised successfully on the M1 suite and fixture. |
| Benchmark compatibility of that toolchain. | **Defer** | No VerilogEval or RTLLM qualification was performed. Do not generalize M1 success to benchmark compatibility or other platforms/Python versions. |

## 9. Recommended correction milestone and re-review checklist

When assigned, Claude Code should complete a small M1 correction milestone. Claim exact paths first; change only what the fixes and regression tests require. Do not alter trusted testbenches or expectations to force a pass.

1. **M1-C1:** enforce the supported trusted-candidate boundary and add the nonce-aware forgery/early-finish non-pass regression. Preserve existing fixture behavior.
2. **M1-C2:** distinguish compiler signal termination from design compilation errors and add the signal regression.
3. **M1-C3:** make owned-process/pipe/thread cleanup exception-safe; test SIGINT and a successful leader leaving a redirected descendant.
4. **M1-I1:** surface capture failures and test log-open/write errors. These changes are closely related to runner cleanup and should be included in the correction if practical.
5. **M1-I2:** align the generated-code execution gate with the first actual model-output execution. Do not start that execution during the correction.
6. Record concrete interface/policy choices and current status under the existing decision process. Avoid broad architecture changes. Address M1-N1/M1-N2 as documented follow-ups if not included immediately.
7. Run the full existing suite plus new regressions with real Icarus, then repeat the no-Icarus configuration. Test counts may increase; report actual counts and explicit skips rather than requiring the old total of 54.
8. Create a fresh example run in a new directory; inspect JSON evidence, source/checker hashes, stage/verdict classifications, and log artifacts. Preserve the old run.
9. Handoff an exact changed-file list, executed commands/results, regression evidence, remaining limitations, decision updates, and a released ownership claim. No check is complete merely because it is listed here.

**Approval gate:** close M1-C1 through M1-C3 with executed evidence; preserve all six original acceptance criteria; explicitly disposition remaining important findings before broader execution. M1 remains unapproved at this review snapshot. Codex should re-review the bounded correction before the team proceeds to M2. No numerical performance claim, benchmark qualification, faculty approval, or M2 authorization is implied by this document.
