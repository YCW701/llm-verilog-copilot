# M1 Implementation Handoff — Corrections for Review R2

Date: **November 8, 2026**  
Milestone: **M1 — Offline Icarus Verification Harness**  
Addresses: [M1_REVIEW_R2.md](M1_REVIEW_R2.md) (verdict CHANGES REQUIRED); issue IDs from [M1_REVIEW.md](M1_REVIEW.md) are preserved  
Author: **Claude Code (implementation)**  
Document type: **implementation handoff — not an independent review and not technical approval**

Every status below is an implementation claim until Codex verifies it in the next review round (normally `M1_REVIEW_R3.md`). M2 has not been started. Nothing was pushed, and no repository or remote was created.

## 1. Summary

- **M1-C1 (critical).** The R2 lone-CR bypass is closed. The correction also found and closed two more bypasses of the same kind. Each was verified to forge a `pass` through public `verify()` against the R2-era screen:
  1. **Backslash + CRLF inside a string literal.** Icarus continues the string across backslash + CRLF. The old screen skipped the backslash and the CR, then ended the string at the LF. Its quote parity then disagreed with Icarus, and later code was hidden from it.
  2. **A number directly before a forbidden construct.** Examples: `#0$display(...)`, `#0$finish`, `#1force`, and `#256tb_adder4.errors = 0`. Icarus lexes the number and the construct as separate tokens. The old screen's "not preceded by an identifier character" lookbehinds counted the digit as part of an identifier and skipped the match.
- **M1-I1 (important).** A version probe that cannot be recorded now stops the run before compilation, as `unknown` / `infrastructure_error`, with the probe evidence kept in the structured result.
- **M1-R2-N1 (non-blocking).** The screen is now described as a restricted supported subset, in `rtl.py`, the README and DECISIONS M1-D4.

## 2. Issue-by-issue status

| Issue | Claimed status | Evidence (executed) |
| --- | --- | --- |
| **M1-C1** — false-pass prevention | **Claimed fixed** (pending R3) | Exact R2 payload: through the CLI, `fail / candidate_policy_violation`, exit 1, not compiled. Through public `verify()` in CR, CRLF and LF forms, the same result. The unscreened inner layer still returns `pass` for the payload, so the regression is meaningful. The differential separator sweep and number-prefix probes are in sections 3–5. |
| **M1-I1** — capture-error propagation | **Claimed fixed** (pending R3) | Injected **open** and **write** failures on version logs, with real Icarus and with stubs, give `unknown / infrastructure_error`. Compile and simulation stay `not_run` with `process: null`; no compile log or `sim.vvp` is written; `version_probe.capture_errors` is populated. A version probe killed by a signal is also blocked. |
| **M1-R2-N1** — restricted subset is not general synthesizability | **Addressed in documentation** | `rtl.py` module docstring, README "How a verdict is decided", DECISIONS M1-D4 amendment. A policy rejection remains the separate `candidate_policy_violation` category. |
| M1-C2 — compiler signal classification | Fixed per R2; unchanged by this correction | Signal-stub regressions still pass (`tests/unit/test_simulation_policy.py`). |
| M1-C3 — process cleanup | Fixed per R2 within POSIX scope; unchanged | `runner` code untouched; SIGINT/SIGTERM/SIGHUP/descendant tests still pass. |
| M1-I2 — generated-RTL execution gate | Fixed per R2; unchanged | Origin-gate tests still pass; `verify()` still requires `origin`. |
| M1-N1 — stale status docs | Fixed per R2; DECISIONS amended (entries still **proposed**) | — |
| M1-N2 — stale example provenance | **New evidence produced** | `runs/adder4-correct-m1-r2-correction-final/` was created after the final source edit. All 12 `code_sha256` entries match the current source (checked by script). `runs/adder4-correct-m1-r2-correction/` is **superseded**: it predates the bounded-output fix in section 4a and differs only in `rtl.py`. It is kept, as are `-v3` and the older runs. |

## 3. Lexer facts verified against Icarus Verilog 13.0

These were probed with `iverilog -g2005` and `vvp -n` on scratch files written with exact bytes. The screen was then changed to match them.

| Context | Icarus 13.0 behavior | Screen behavior now |
| --- | --- | --- |
| `//` comment followed by LF, CR or CRLF | The comment ends there; code after it is compiled | The comment ends there; code after it is screened |
| `//` comment followed by VT, FF, other C0 controls, DEL, NEL, U+2028 or U+2029 | The comment **continues** | The comment continues. Treating these as line ends would let a later `/*` hide code, which the sweep covers |
| `"…` followed by a raw LF or CR | Compile error: "Missing closing quote" | Rejected: string is not closed on its line |
| `"…\` followed by LF, CR or CRLF | The string **continues** onto the next line | Rejected: line continuation inside a string literal is not supported |
| `"…` followed by VT, FF and similar | The string continues | The string continues |
| `/*/` | Does not close the comment | Does not close the comment |
| `//` or `/*` inside a string | Not a comment | Not a comment |
| `#0$display`, `#1force`, `#256tb_adder4.errors = 0` | Number token, then the construct; compiles and runs | Detected |

## 4. Deliberate behavior changes for the reviewer to rule on

1. **`$` inside identifiers is now rejected**, e.g. `wire a$b;`. R2 saw it admitted and called it benign. It is legal Verilog, but a `$` directly after an identifier character or digit can no longer be told apart from `#0$display` without a full number lexer. The test moved openly from the admitted list to the rejected list in `tests/unit/test_rtl_policy.py`.
2. **Identifiers that end in `force`, `release` or `defparam` are rejected**, e.g. `enforce`. Identifiers that contain these words followed by more characters, such as `forced` or `release_n`, are still admitted, and a test covers both cases.
3. **A dotted name preceded by a digit counts as a hierarchical reference**, e.g. `#0tb.x`. Real literals such as `1.5` and `2.0e-3` are unaffected; a test covers them.
4. **Unterminated strings are policy violations.** Icarus rejects them as compile errors, so the verdict is still `fail`; only the category changes.
5. **Schema version is now "3".** It adds `StageResult.version_probe` (a `ProcessResult`). See DECISIONS M1-D6.
6. **A non-zero exit from a version probe is recorded but does not block.** Only spawn, capture, timeout, signal and log-read failures block. Icarus 13.0 exits 0 for both `-V` probes; other builds are untested, so this is a portability assumption. A probe that prints no recognizable version line is recorded as `tool_version: null` with empty `capture_errors`, so it can be told apart from a capture failure.

All of these remain **proposals** under DECISIONS M1-D4 and M1-D6 until the team adopts them.

## 4a. Regression introduced by this correction, found and fixed before handoff

The new string-literal checks first added their problems to the screen's output without the 20-violation cap. A roughly 1 MiB candidate of repeated `"` + LF returned **358,400** violations. The CLI would have printed all of them, and `verification.json` would have stored all of them. This broke the documented bound and CLAUDE.md's bounded-artifact rule. Advisor review caught it before handoff, and it was confirmed by executing exactly that input.

The fix sends the lexical problems through the same capped loop as the token violations (`itertools.chain`) and stops collecting them after the cap plus one. The bounded-output test now covers the string floods `"`+LF, `"`+backslash+LF and `"`+CR, as well as the original `$a ` flood and `/*`. With the cap removed (scratch mutation D), the three string-flood cases fail.

## 5. Executed commands and results

Environment: macOS (Darwin 27.2.0), Python 3.14.6, the existing `.venv` with pytest, Icarus Verilog 13.0 (stable). `PYTHONDONTWRITEBYTECODE=1`, pytest cache disabled, temporary directories outside the project.

| Command (from project root) | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider --basetemp <scratch>/pt-final-with` | **287 passed** in 30.86 s, exit 0, 0 skipped |
| `PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -rs --basetemp <scratch>/pt-final-without` | **239 passed, 48 skipped** in 4.09 s, exit 0. Every skip is labeled `SKIPPED: iverilog and/or vvp not found on PATH` (checked by grep: 0 other reasons); skips are not passes. |
| `.venv/bin/python -m verilog_copilot verify --rtl tests/fixtures/adder4/candidates/correct.v --task adder4 --output runs/adder4-correct-m1-r2-correction-final` | `pass / none`, screen `ok`, exit 0 (final evidence run) |
| The same CLI on the exact R2 lone-CR payload, written with `write_bytes` and checked to contain `?\r` | `fail / candidate_policy_violation`, compile `not_run`, exit 1; 4 violations listed (`$value`, `$plusargs`, `$display`, `$finish`) |

The CR-payload CLI check ran before the section 4a fix, which changed only the output cap; the payload's 4 violations are below the cap. The suite grew from 130 to 287 tests. Most of the increase comes from parametrized cases.

### New regressions

**`tests/unit/test_rtl_policy.py`** (pure screen, byte payloads):
- the exact R2 payload;
- LF, CRLF and CR forms give identical violations and line numbers, for the payload and for five fixtures;
- a `//` comment ends at LF and CR, and does not end at any of 33 other separators;
- a comment followed by `/*` is aligned with Icarus for all 36 separators;
- string-separator variants;
- backslash + LF/CR/CRLF continuation;
- raw line ends inside strings;
- 12 number-prefix constructs;
- keyword-suffix and real-number boundary cases.

**`tests/integration/test_icarus_verify.py`** (real Icarus, public path):
- the exact R2 payload in CR, CRLF and LF forms. The test asserts the inner layer is fooled and the public path rejects the candidate before compilation, keeping a byte-exact `candidate.v`.
- A **differential separator sweep**: 4 templates × 36 separators (33 non-terminators plus LF, CR and CRLF). Whenever the unscreened inner layer returns `pass` (Icarus really runs the forgery), the public path must return `candidate_policy_violation`, and the public path never passes. The set of separators that produce a live forgery is also asserted, so the sweep provably exercises real forgeries.
- Number-prefixed system-task and hierarchical forgeries, each asserted live on the inner layer.
- Benign `correct.v` and `wrong_behavior.v` in LF, CRLF and CR forms keep `pass` and `test_mismatch`.
- Version-log open and write failures cannot pass.
- Normal version-probe evidence is recorded.

**`tests/unit/test_simulation_policy.py`** (shell stubs, no Icarus):
- a version probe killed by a signal;
- open and write capture failures;
- an unrecognized version string that does not block;
- a non-zero probe exit that does not block.

### Mutation checks

These ran on scratch copies under the session scratchpad, not in the project, and are not part of the suite.

| Mutation | Result |
| --- | --- |
| **C, verbatim R2-era `rtl.py`** | 5 of 9 public-path regressions failed, each a forged **pass**: `r2_lone_cr_payload[cr]`, `differential_sweep[comment]` (first failure CR), `differential_sweep[string_continuation]` (first failure CRLF), and both `number_prefixed_forgeries`. This confirms the two newly found bypasses were live in the R2 code. |
| **A, partial lexer revert** | 22 failures: 17 screen unit tests and 5 Icarus integration tests. |
| **B, version-probe errors ignored** | 5 failures: 3 unit and 2 integration. |
| **D, lexical-problem cap removed** | 3 failures: the string-flood cases of `test_violation_output_is_bounded_and_fast`. |

## 6. Changed files

| File | Change |
| --- | --- |
| `src/verilog_copilot/rtl.py` | Icarus-aligned line ends (LF and CR); string-literal scan via `_scan_string` that rejects continuations and unclosed strings; `$`, keyword and hierarchical rules without the digit/identifier exemption; CR-aware line numbers; one shared output cap for lexical and token violations; restricted-subset docstring |
| `src/verilog_copilot/models.py` | `SCHEMA_VERSION = "3"`; `StageResult.version_probe` |
| `src/verilog_copilot/tools/icarus.py` | `VersionProbe` dataclass; `probe_version` returns process evidence plus an `error` field for spawn, capture, timeout, signal and log-read failures |
| `src/verilog_copilot/tools/simulation.py` | Version-probe preflight: records evidence on both stages and blocks before compilation on probe error; docstring |
| `tests/unit/test_rtl_policy.py` | New C1 regressions; `a$b` moved from admitted to rejected (deliberate) |
| `tests/unit/test_simulation_policy.py` | New I1 stub regressions |
| `tests/integration/test_icarus_verify.py` | New C1 and I1 public-path regressions |
| `tests/integration/test_cli_end_to_end.py` | Expects schema `"3"` |
| `README.md` | R2 status note, restricted subset, lexing rules, version-probe rule, schema 3 |
| `docs/DECISIONS.md` | M1-D4 and M1-D6 amendments (still proposed) |
| `docs/reviews/M1_HANDOFF_R2.md` | This handoff (new) |
| `docs/reviews/README.md` | Implementation-handoff link only |
| `docs/ROADMAP.md` | This correction's ledger row only |
| `runs/adder4-correct-m1-r2-correction-final/` | Final evidence run (generated output) |
| `runs/adder4-correct-m1-r2-correction/` | Intermediate evidence run, superseded by `-final` (see section 4a) |

Not modified:
- the trusted checker `tb_adder4.v` (sha256 `0436fdfb2619…`, matches the registry pin);
- the six original candidates and the three earlier correction fixtures (hashes rechecked);
- `AGENTS.md`, `CLAUDE.md`, `M1_REVIEW.md`, `M1_REVIEW_R2.md`;
- `process.py`, `cli.py`, `storage.py`, `local_fixtures.py`;
- existing `runs/` directories.

## 7. Remaining limitations (not claimed solved)

- **The screen is lexical.** It is aligned with Icarus 13.0 for the probed comment, string and number cases, but it is not a parser and not proven complete against every interference vector. Other Icarus versions may lex differently and are untested.
- **Version-specific sweep.** The differential sweep asserts which separators produce a live forgery under Icarus 13.0. On another Icarus version, a failure in that assertion means lexer alignment must be re-verified, not necessarily that the screen regressed.
- **Restricted subset.** Legal RTL is rejected (section 4 and R2-N1). The team must revisit this before benchmark evaluation (M4).
- **No sandbox.** The execution gate for model-generated RTL is unchanged (Q05). The origin field is caller-declared.
- **Process cleanup scope** is unchanged: SIGKILL to the harness, descendants that call `setsid`, and non-POSIX platforms are not covered.
- **Compiler diagnostics** can still reveal trusted checker paths and lines; sanitize them before M3 uses them as feedback.
- **Line endings in git.** No `.gitattributes` exists yet. The new CR and CRLF tests build their payloads in code, so clone normalization cannot weaken them, but the testbench hash pin still assumes LF bytes.
- **Coverage scope.** Only Python 3.14.6 on macOS with Icarus 13.0 has been exercised.

## 8. Ownership release and next bounded task

All editing claims for this correction are **released** in the [ROADMAP](../ROADMAP.md) ledger row "M1 R2 correction".

Next bounded task: **Codex independent re-review, saved as `M1_REVIEW_R3.md`.** Suggested verification:
1. Reproduce the R2 lone-CR and version-write probes against the current code.
2. Rerun the mutation-C comparison, or an equivalent comparison against the R2 snapshot.
3. Rule on the tightenings in section 4.
4. Confirm that C2, C3, I2 and the original six acceptance areas still hold.

M2 must not start until M1 is approved.
