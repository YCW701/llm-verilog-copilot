# Independent M1 Re-review — Round 2

Date: **November 8, 2026**  
Milestone: **M1 — Offline Icarus Verification Harness**  
Review round: **R2**  
Reviewer: **Codex — Software Architect and Technical Reviewer**  
Overall verdict: **CHANGES REQUIRED**  
Previous report: [M1_REVIEW.md](M1_REVIEW.md), the preserved original R1 report

## 1. Disposition and scope

C2 and C3 are fixed, and the correction tests provide meaningful evidence. A new line-ending bypass leaves C1 unresolved. I1 is fixed for compilation/simulation capture but remains unresolved for tool-version capture. These remaining gaps require corrections and independent re-review before M1 is technically approved and the team proceeds to M2.

This is a saved record of the most recent independent re-review, not a new test run. Saving it does not change implementation or authorize M2. Source line numbers refer to the implementation inspected during R2 and may shift after corrections. Recommendations are reviewer recommendations, not confirmed team or faculty decisions.

The re-review read the original report, project instructions, correction documentation, implementation, regression tests, fixture registry, and current example artifacts. It independently executed the existing suite and targeted temporary probes. No project files were modified, no dependencies were installed, no model calls or benchmark campaign ran, and M2 was not started. A final inventory/hash comparison confirmed all 90 reviewed project files were unchanged during the re-review.

## 2. Independently executed tests and artifact checks

Environment: existing local `.venv`, macOS, Python **3.14.6**, pytest **9.2.0**, Icarus Verilog/runtime **13.0 stable**. The wrapper set `PYTHONDONTWRITEBYTECODE=1`; pytest cache writes were disabled and temporary artifacts were outside the project.

### Full suite with Icarus

From the project root:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp /private/tmp/capstone-m1-rereview-czgpme0s/with-icarus
```

**Observed: 130 passed in 11.79 seconds, exit code 0.** This includes 30 real-Icarus integration tests and 100 unit tests. No tests were skipped in this configuration.

### Suite with Icarus unavailable through PATH

```bash
PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp /private/tmp/capstone-m1-rereview-czgpme0s/without-icarus
```

**Observed: 100 passed, 30 explicitly skipped in 3.22 seconds, exit code 0.** The integration skips identify missing Icarus tools. They are not passes.

### Independent probes and provenance

| Check | Verified result |
| --- | --- |
| Nonce forgery hidden after a lone CR inside a line the screen considers a comment | Screen reports no violations; public `verify()` returns `pass / none` for a wrong DUT. See M1-C1 below. |
| Inject write failures into version-log pumps only | Verification still returns `pass / none`; both tool versions are null. See M1-I1 below. |
| Ordinary named-port submodule connections | Screen admits the candidate; all 256 vectors pass. |
| Ordinary identifier containing `$`, such as `result$display` | Screen admits the candidate; all 256 vectors pass. |
| Local generate-scope reference `g.x` | Screen rejects it; direct Icarus qualification compiles and passes all 256 vectors. |
| Candidate using `` `default_nettype none `` | Screen rejects it; direct Icarus qualification compiles and passes all 256 vectors. |
| Unqualified attempted upward checker-variable access | Screen admits it, but compilation fails; this probe did not yield a bypass. |
| Source hashes in `runs/adder4-correct-m1-correction-v3/manifest.json` | All recorded implementation source hashes match current files. |
| Original checker and six original candidates compared with the R1 snapshot | All seven files are unchanged. |

Local evidence was saved under `/private/tmp/capstone-m1-rereview-czgpme0s/`, including `with-icarus.txt`, `without-icarus.txt`, `targeted-results.json`, raw byte-preserving candidates, and probe run directories. These temporary paths may be cleaned later; the material evidence and reproduction details are recorded below. None of the targeted probes were added to project tests during the read-only review.

## 3. Previous-issue tracking

| Original issue | R2 status | Independent assessment |
| --- | --- | --- |
| **M1-C1 — False-pass prevention** | **Unresolved** | Original nonce and hierarchical-tamper fixtures are rejected before compilation, but the new lone-CR variant bypasses screening and falsely passes. |
| **M1-C2 — Compiler signal classification** | **Fixed** | Real signal-terminated compiler/simulator stubs produce infrastructure/unknown. Ordinary compilation errors remain failures. |
| **M1-C3 — Process cleanup** | **Fixed within the documented POSIX scope** | Executed tests cover SIGINT, a redirected descendant after successful leader exit, timeout cleanup, and CLI SIGTERM/SIGHUP cleanup. |
| **M1-I1 — Capture-error propagation** | **Unresolved; partially corrected** | Runner and compilation/simulation propagation work. Tool-version probe capture errors are discarded and still permit a pass. |
| **M1-I2 — Generated-RTL execution gate** | **Fixed for M1's declared-origin contract** | Required `origin` rejects model-generated candidates before copying or tool execution. Documentation applies the gate before first generated-code execution. Authorship is caller-declared, not independently proven. |
| **M1-N1 — Stale documentation status** | **Fixed for the reported status gap** | Current-status notes and proposed M1 decision entries distinguish implementation from the historical baseline. Proposed choices still need the appropriate team confirmation. |
| **M1-N2 — Stale example provenance** | **Fixed with new evidence** | The `-v3` example matches current implementation hashes; older runs are preserved. Corrections after R2 will require fresh evidence again. |

## 4. Critical finding: M1-C1 remains unresolved

### Lone carriage return bypasses the RTL admission screen

**Severity: Critical — blocks M1 technical approval and progression to M2.**

**Relevant locations:** [rtl.py:59](../../src/verilog_copilot/rtl.py#L59), especially the `text.find("\n", i)` line-comment scan at line 60; candidate admission in [tools/simulation.py:217](../../src/verilog_copilot/tools/simulation.py#L217).

**Verified evidence:** the screen ends `//` comments only at LF (`\n`). In the tested Icarus 13.0 toolchain, a lone CR (`\r`) also ends the comment. The following byte payload was written to a temporary candidate with `Path.write_bytes()`, preserving the CR:

```python
payload = (
    b"module adder4(input [3:0] a,b,output [4:0] sum);\n"
    b"assign sum=0; // ignored?\r"
    b"reg [511:0] n; initial begin "
    b'if ($value$plusargs("checker_nonce=%s",n)) '
    b'$display("CHECKER_RESULT nonce=%0s checks=256 errors=0",n); '
    b"$finish; end\nendmodule\n"
)
candidate.write_bytes(payload)
```

The source after CR is hidden from the screen but executed by Icarus. The reviewer invoked public `verify()` with the registered `adder4` bundle, fresh run directory, discovered Icarus tools, and `origin=CandidateOrigin.TEAM_AUTHORED`.

Observed results:

```text
screen_candidate_rtl(payload): []
verdict: pass
category: none
message: checker confirmed 256/256 vectors with 0 errors
```

The candidate always drives zero and finishes before checker completion. It is functionally wrong. Trusted checker contents were not modified.

**Consequence:** the lexical screen does not reliably block the original forgery vector, even though the LF-only fixture is rejected and all supplied tests pass. A passing checker-result string still cannot establish correct execution when candidate code is hidden from the screen by lexer disagreement.

**Recommended fix:** make comment/string scanning handle line endings consistently with Icarus. Add byte-preserving regressions for LF, CRLF, and lone CR. Exercise public `verify()` as well as the screen function; do not rely on a text fixture read/write path that normalizes line endings. Preserve the exact relationship between screened and compiled candidate bytes. Do not weaken or modify the trusted checker to accommodate the probe.

**Acceptance for next re-review:** the exact payload cannot pass; the forbidden constructs after CR are detected or the candidate is rejected under a documented supported-byte policy, before compilation. Equivalent LF/CRLF/CR forms receive consistent intended classifications, benign valid variants remain admitted, and the existing nonce/hierarchy regressions still pass.

## 5. Important finding: M1-I1 remains unresolved for version capture

### Tool-version probe capture failures are discarded

**Severity: Important — include in the next correction and re-review.**

**Relevant locations:** [tools/icarus.py:50](../../src/verilog_copilot/tools/icarus.py#L50), especially the result checks at line 62; probe consumption in [tools/simulation.py:237](../../src/verilog_copilot/tools/simulation.py#L237).

**Verified evidence:** the reviewer temporarily patched `_BoundedPump._write_chunk` in memory to raise an `OSError` only when the destination filename contained `.version.`. Compilation and simulation capture remained unmodified:

```python
real_write = process._BoundedPump._write_chunk

def bad_version_write(self, out, data):
    if ".version." in self._dest.name:
        raise OSError("review simulated version log write failure")
    return real_write(self, out, data)

# Within patch.object(process._BoundedPump, "_write_chunk", bad_version_write),
# verify the existing correct.v through public verify() with TEAM_AUTHORED origin.
```

Observed result:

```text
verdict: pass
category: none
compile.tool_version: null
simulation.tool_version: null
```

The runner records capture failures, but `probe_version()` checks spawn/timeout conditions without propagating `capture_errors`. Its caller therefore cannot distinguish missing version evidence from a successful probe.

**Consequence:** required provenance can be lost while verification reports pass. This leaves the original capture-error requirement only partly satisfied. The existing simulation-write regression does not exercise version capture.

**Recommended fix:** propagate version-probe capture failures into structured verification evidence and return infrastructure/unknown when required capture fails. Keep the fix within the existing runner/adapter contracts; a new framework is unnecessary. Preserve raw evidence and distinguish a recorded capture failure from a merely unrecognized version string.

**Acceptance for next re-review:** injected version-log open/write failures cannot produce pass, are visible in structured results, and leave compilation/simulation appropriately not run after failed preflight. Existing compile/simulation capture-error tests and normal version recording continue to pass.

## 6. RTL policy, classifications, and regression quality

### Non-blocking clarification: M1-R2-N1 — restricted subset is not general synthesizability

**Relevant locations:** [rtl.py:17](../../src/verilog_copilot/rtl.py#L17) and the RTL admission-screen explanation in [README.md](../../README.md).

**Verified evidence:** both a local generate-scope reference and `` `default_nettype none `` were rejected as policy violations, but compiled under Icarus `-g2005` and passed all 256 checker vectors when directly qualified. Named-port connections and an ordinary identifier containing `$` were admitted and passed.

**Assessment:** these conservative exclusions can be accepted for the restricted M1 subset, but should not be described as proof that all rejected constructs are testbench-only or unsynthesizable. Policy rejection is distinct from functional mismatch. Broader benchmark compatibility was not tested.

**Recommendation and acceptance:** clarify the restricted supported subset in documentation, retain a separate policy-violation category, and have the team adopt/revisit the scope before benchmark evaluation. Add representative legal-RTL examples when expanding it. No broad policy relaxation or parser rewrite is requested by R2.

### Changed CLI classifications are acceptable under the adopted admission policy

`early_finish`, `fake_pass`, and the original flooding `hang` now return `fail / candidate_policy_violation` before compilation. This is acceptable provided the team adopts the admission policy and keeps the stage/reason explicit. It does not claim their old dynamic behavior was simulated through the public path.

Executed tests provide separate coverage:

- Public-path tests assert policy rejection and that compilation/simulation do not run.
- Explicitly isolated inner-layer tests retain `checker_inconclusive`, `test_mismatch`, and flooding `simulation_timeout` behavior for the original fixtures.
- `hang_silent` exercises a real timeout through the supported public path.
- Signal regressions use actual terminated stubs, not only fabricated result objects.
- Capture tests cover failed log opening and simulated writes while draining output; an integration test confirms simulation capture failure cannot pass.
- The model-origin test uses a marker-producing tool stub and verifies no tool execution or copied candidate.

These are meaningful checks, not merely revised expectations concealing lost coverage. Their missing cases are the CR lexer mismatch and version-probe propagation documented above. A private test-only path is not authorization to bypass screening in application callers.

## 7. Remaining limitations and boundaries

- **Verified M1 boundary:** declared `MODEL_GENERATED` input is refused. The required origin enum is an API tripwire, not proof of authorship; the CLI declares team-authored input. M2 callers must preserve actual provenance rather than relabel model output.
- **Documented process scope:** cleanup covers the owned POSIX process group. Descendants escaping through `setsid`, SIGKILL to the harness, and other platforms remain outside those guarantees. R2 does not claim those cases are solved.
- **Untested/general risk:** the lexical screen is conservative and not proven complete against all interference vectors. Passing selected probes would not establish a security sandbox or authenticated oracle.
- **Execution gate remains:** no model-generated RTL may execute until the applicable isolation policy is adopted and validated. Host isolation and same-simulator interference are separate concerns. No full sandbox implementation is requested in this correction.
- **Unverified scope:** Python/Icarus success here does not qualify VerilogEval, RTLLM, other tool versions, or other operating systems. No benchmark or live provider efficacy claim is supported.
- **Decision authority:** proposed M1 decisions remain proposals. Independent technical approval, when earned, does not replace team approval of major architectural decisions.

## 8. Prioritized action items and next re-review acceptance

Claude Code's next assignment should remain a bounded M1 correction. Read this report and R1 as needed, then claim exact file paths in the roadmap ledger before editing.

1. **Critical — M1-C1:** close the CR comment bypass with line-ending-consistent lexing and byte-preserving public-path regression tests.
2. **Important — M1-I1:** propagate version-probe capture errors into infrastructure/unknown results, with focused tests.
3. **Non-blocking — M1-R2-N1:** describe the RTL policy as a restricted supported subset; preserve policy rejection as distinct from functional mismatch.
4. Run the full suite with Icarus and the no-Icarus configuration. Record actual commands, counts, failures/skips, and targeted regression results. New totals may exceed 130; do not substitute the old count for actual execution.
5. Preserve the original checker, historical reports, and existing artifacts. Create fresh evidence in a new run directory after the final source change; verify its manifest hashes match the corrected source.
6. Save an implementation handoff summary identifying the addressed report, changed files, claimed issue statuses, executed validation, remaining limitations, and released ownership. Do not start M2.

For the next independent review, Codex must verify closure of C1 and I1 using the reproduced failures, confirm C2/C3 and the execution gate remain intact, verify the six original M1 acceptance areas, and distinguish any deferred/non-blocking limitations explicitly. Save that assessment as a new review round rather than editing this report. **M1 remains unapproved at the R2 snapshot: CHANGES REQUIRED.**
