# M1 Publication Verification — Review Round 4

Date: **November 11, 2026**<br>
Milestone: **M1 — Offline Icarus Verification Harness**<br>
Round: **R4**<br>
Reviewer: **Codex — Software Architect and Technical Reviewer**<br>
Verdict: **APPROVED WITH NON-BLOCKING ISSUES** for the existing qualified M1 scope<br>
Previous independent review: [M1_REVIEW_R3.md](M1_REVIEW_R3.md)

## 1. Scope and authorization

The team explicitly requested organizing and publishing the existing M1 project to `https://github.com/YCW701/llm-verilog-copilot`, committing/pushing `main`, and creating/pushing `m1-baseline` after branch-push verification. Current project information is **Group 62, three students, Professor Hang Liu, academic year 2026–2027**. This supersedes the earlier four-student/no-publication constraints for this task, not the ban on starting M2 without an assignment.

The workspace already had an appropriate setuptools `src/` Python structure and local M1 commit `7b4fbbe`. The GitHub starter history contains only a README and Python `.gitignore` at `097c7f1`. Preserve both histories through normal integration; do not force-push or replace M1 code with a fresh implementation. The local source, tests, fixtures, packaging, `.gitattributes`, historical reports, and pre-existing uncommitted M2 plan are preserved. README/current project metadata, ignore rules, ownership/publication records and this new review are documentation/organization changes only.

The existing M2 plan remains proposed documentation, not implementation; its four-role staffing assumptions require adjustment for the current team. No new provider, repair, training, distributed-computing, GPU, benchmark, synthesis, or FPGA functionality is introduced.

This report records executed local verification before publication. It does not assert an unexecuted push or tag operation; branch/tag hashes are verified and reported in the task's final handoff after the Git operations complete.

## 2. M1 inventory and implemented behavior

The original committed M1 inventory consists of **47 tracked files**: 12 package Python files, 9 Python test/config files, 10 Verilog fixture files (one checker and nine candidates), `pyproject.toml`, root instructions/README/Git attributes/ignore files, and project/review documentation. The separately preserved `docs/milestones/M2_PLAN.md` is future planning, not M1 application code.

| Existing component | Actually implemented |
| --- | --- |
| `src/verilog_copilot/{__init__,__main__,cli}.py` | Package version, module/console entry point, the `verify` subcommand, validated CLI limits, outcome/usage/signal exit codes. |
| `models.py` | Stage/process/checker/file/verification records; schema 3, explicit verdict/category/origin, version-probe and capture-error evidence. |
| `rtl.py` | Conservative lexical admission screen with CR/LF/string/number-prefix handling and bounded violation counts. No natural-language generation or general Verilog parser. |
| `storage.py` | SHA-256 hashing, new run-directory allocation, exclusive candidate copies, atomic collision-refusing JSON publication. |
| `benchmarks/local_fixtures.py` | Local synthetic adder4 registry, pinned checker hash, trusted verdict interpreter. No VerilogEval/RTLLM adapter. |
| `tools/process.py` | Fixed argument-list processes, minimal environment, timeouts, bounded stream capture, capture errors, owned POSIX process-group cleanup. |
| `tools/icarus.py` | Tool discovery, `-V` probe evidence, fixed compiler/simulator arguments. No Verilator execution backend. |
| `tools/simulation.py` | Required-origin gate, byte-copy/screen/integrity checks, version preflight, real compile/simulation, trusted outcome classification. |
| `tests/fixtures/adder4/` | Exhaustive 256-pair checker and nine controlled candidates for correctness, syntax, behavior, policy, early finish, hangs and forgery cases. |

Natural-language RTL generation, runtime LLM providers, repair loops, benchmarks, pass@k reports, synthesis/STA and FPGA deployment remain unimplemented. Future architecture diagrams and plans do not prove those features exist. No runtime API key or GPU is needed for M1.

## 3. Independently executed tests

Environment: existing `.venv`, macOS, Python **3.14.6**, pytest **9.2.0**, Icarus compiler/runtime **13.0 stable**. No dependency installation was performed. Artifacts/logs were placed under `/private/tmp/capstone-publish-sdohncdt/`, outside the repository.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp /private/tmp/capstone-publish-sdohncdt/with-icarus
```

**Observed: 287 passed in 28.55 seconds, exit code 0, zero skips.**

```bash
PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp /private/tmp/capstone-publish-sdohncdt/without-icarus
```

**Observed: 239 passed, 48 explicitly skipped in 3.89 seconds, exit code 0.** The skips identify unavailable Icarus tools and are not passes.

```bash
.venv/bin/python -B -m verilog_copilot verify \
  --rtl tests/fixtures/adder4/candidates/correct.v --task adder4 \
  --output /private/tmp/capstone-publish-sdohncdt/fresh-cli
```

**Observed:** exit 0, compile/simulation `ok`, checker-confirmed **256/256 vectors with zero errors**, schema 3, and all 12 recorded source hashes matching the existing implementation. The output directory was fresh. Existing local run directories were not overwritten or staged for upload.

The full suite exercises the six original M1 acceptance areas: explicit correct-fixture pass/evidence; mismatch/syntax classification; timeouts/bounded logs/process cleanup; missing-tool and false-pass defenses; collision/integrity/literal-path handling; and offline tests with explicit real-tool skips. Tests also rerun the CR/string/number-prefix regressions, compiler-signal distinction, capture-error preflight and declared model-origin gate. These facts support the controlled M1 scope only, not arbitrary RTL correctness or a security sandbox.

**Clean-checkout layout verification:** exported the prepared local commit with `git archive HEAD` into `/private/tmp/capstone-publish-sdohncdt/clean-checkout`, containing no workspace caches, local run evidence or virtual environment. Ran the existing workspace `.venv/bin/python -m pytest -p no:cacheprovider --basetemp /private/tmp/capstone-publish-sdohncdt/clean-checkout-pytest` with that export as the working directory and bytecode disabled. **287 passed in 28.40 seconds, exit 0.** Pytest used the exported `src/` and fixture tree. This verifies checkout-relative layout with the existing interpreter/dependencies; it is not a fresh dependency-installation test.

Initial dependency installation from PyPI, other operating systems/Python versions, live model calls, benchmark performance and synthesis metrics were **not tested**. No numerical efficacy claim is made.

## 4. Previous findings and limitations

| ID | Publication-review status | Evidence / action |
| --- | --- | --- |
| M1-C1 | **Fixed for the reported vectors and declared M1 subset; retained** | Unchanged reviewed screen; complete real-Icarus regression suite passed. No universal hostile-RTL claim. |
| M1-C2 | **Fixed; retained** | Compiler/runtime signal-stub tests passed; infrastructure conditions remain distinct from compilation defects. |
| M1-C3 | **Fixed within documented POSIX scope; retained** | Timeout/descendant/SIGINT and CLI termination tests passed. SIGKILL and descendants leaving the process group remain outside the guarantee. |
| M1-I1 | **Fixed for reported capture failures; retained** | Version/compile/simulation capture-error tests passed. |
| M1-I2 | **Fixed for caller-declared-origin contract; retained** | Model-generated origin remains blocked; no isolation policy was invented or lifted. |
| M1-N1 / M1-N2 / M1-R2-N1 | **Fixed as previously scoped; retained** | Current documentation distinguishes implementation from plans and policy rejection from functional mismatch; older examples/reports remain historical. |
| M1-R3-N1 / FU-M1-1 | **Deferred, minor** | Same-basename explicit wrappers can overwrite version-probe logs at [icarus.py:70](../../src/verilog_copilot/tools/icarus.py#L70). Default distinct `iverilog`/`vvp` names are used. Fix before relying on such wrappers; R3 closure criteria remain applicable. |
| M1-R3-N2 / FU-M1-2 | **Deferred, minor** | [models.py:36](../../src/verilog_copilot/models.py#L36) still describes every `fail` as a design defect. README clarifies category semantics; source is intentionally unchanged. Clarify under a separately owned result-contract update. |

**Additional verified documentation limitation, minor:** [cli.py:133](../../src/verilog_copilot/cli.py#L133) still emits `code_revision=None`. The existing source-hash evidence is usable; README now discloses the missing automatic Git revision. Preserve the implementation in this publication; add proper revision/dirty-state capture only under a future assigned/reviewed change.

The lexical policy, nonce, source hash and temporary directory do not provide complete filesystem/network/resource isolation or authenticated oracle separation. Only reviewed team-authored fixtures belong in the supported execution path. The CLI's team-authored declaration is not proof of authorship. Model-generated RTL stays blocked until an execution policy is adopted and validated.

## 5. Publication organization and restrictions

- Keep the existing source/test structure; no nested project or clone is needed because the workspace is already a Git repository. Attach the requested remote, preserve its starter commit, and integrate without rewriting existing history.
- Preserve the complete local ignore rules and append the remote Python starter rules plus environment-variant, credential/key and simulator-output exclusions. Keep byte-exact Verilog attributes.
- Retain the existing uncommitted M2 plan and its roadmap entry as clearly labeled planning. Current metadata uses three students; historical reviews retain their original dated team descriptions. The current three-role document is a proposal, not named student assignments.
- Update Codex/Claude publication wording identically: explicit user authorization permits this push/tag task, while ownership, immutable reviews and no-M2 implementation constraints remain.
- Keep `.env`/credential contents, local agent state, `.venv`, caches and `runs/` out of the staged tree. Inspect candidate files/history for obvious credential material without printing any matched secret values. An ignore policy is not a guarantee against secrets embedded in arbitrary tracked text.
- Push `main` without force after integration and local checks; verify the exact remote head before creating/pushing `m1-baseline`. Do not move an existing tag or overwrite concurrent remote work. Preserve both root histories in the published ancestry.

## 6. Acceptance and final handoff

The M1 source/test/fixture hashes must remain identical to local baseline `7b4fbbe`. Historical reviews, existing M2 plan bytes, packaging and `.gitattributes` must also remain unchanged. Documentation/ignore updates must pass link/Markdown checks and `git diff --check`; the shared agent contract must remain identical. Check the exact staged paths and all reachable history before upload.

The publication task completes only when the remote `main` SHA equals the final local integration commit, `m1-baseline` resolves remotely to that same commit, both original histories are ancestors, and the working tree has no unintended changes. The final user-facing handoff must state the repository URL, exact commit/tag, actual test results, implemented-versus-planned scope, and retained limitations. A failed/unexecuted push, tag, or test must be reported as such.

No M1 code correction is required to publish the demonstrated default-tool baseline. The non-blocking follow-ups remain separately assigned work, not silent changes to the approved application. Technical approval still does not confirm proposed architecture decisions for the team or faculty.
