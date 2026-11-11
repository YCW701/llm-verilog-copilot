# An LLM Copilot for Verilog Design

Rutgers ECE Capstone, **Group 62 — 3 students**<br>
Advisor: **Professor Hang Liu**<br>
Academic year: **2026–2027**<br>
Repository: [YCW701/llm-verilog-copilot](https://github.com/YCW701/llm-verilog-copilot)

This project aims to build a copilot for Verilog RTL generation and simulation-guided repair. **The implemented baseline is M1: an offline verification harness for supplied, team-authored RTL.** It does not yet generate RTL from natural language or call an LLM. Planning documents live in [docs/](docs/); start with [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md).

**Current status: milestone M1 (offline verification harness) is technically approved** by the independent review [docs/reviews/M1_REVIEW_R3.md](docs/reviews/M1_REVIEW_R3.md) (APPROVED WITH NON-BLOCKING ISSUES), for team-authored RTL in the restricted subset on the exercised macOS / Python 3.14.6 / Icarus 13.0 setup. The team has not yet confirmed the M1 decisions (DECISIONS section 6), and M2 has not started. The package can compile and simulate a team-authored Verilog file against a trusted, hash-pinned fixture checker using Icarus Verilog. It records structured JSON evidence for every run. There is no LLM generation, provider, or repair loop yet; those arrive in M2/M3 (see [docs/ROADMAP.md](docs/ROADMAP.md)).

The M1 correction after the independent review ([docs/reviews/M1_REVIEW.md](docs/reviews/M1_REVIEW.md)) added three things:
- an enforced RTL admission screen;
- an explicit execution gate that refuses model-generated RTL;
- exception-safe process cleanup and structured log-capture errors.

The R2 correction ([docs/reviews/M1_REVIEW_R2.md](docs/reviews/M1_REVIEW_R2.md), handoff [docs/reviews/M1_HANDOFF_R2.md](docs/reviews/M1_HANDOFF_R2.md)) changed two things. It aligned the screen's comment and string lexing with Icarus, closing the lone-CR, string-continuation and number-prefix bypasses. Version-probe capture failures now also block a verdict.

**Only team-authored RTL may be executed.** Running model-generated RTL stays blocked until an execution-safety policy is adopted and validated (DECISIONS Q05).

## Current implementation and repository structure

The existing source layout is retained; no M1 application modules or testbenches were moved or rewritten for GitHub publication. Local M1 history begins at `7b4fbbe` and is preserved alongside the repository's starter history. The `m1-baseline` tag identifies the published baseline after push verification.

```text
llm-verilog-copilot/
  pyproject.toml                 # setuptools package and pytest configuration
  README.md
  AGENTS.md                      # Codex project and review workflow
  CLAUDE.md                      # Claude Code, same shared project contract
  .gitignore                     # local + remote starter rules; credentials/artifacts excluded
  .gitattributes                 # preserve byte-exact Verilog line endings
  src/verilog_copilot/
    __init__.py, __main__.py      # package version and Python module entry point
    cli.py                       # verify command and exit/signal handling
    models.py                    # schema-3 verification/process records
    rtl.py                       # conservative lexical admission screen
    storage.py                   # hashes and collision-refusing artifact publication
    benchmarks/local_fixtures.py # adder4 task and pinned trusted checker
    tools/process.py             # bounded subprocess runner and capture-error evidence
    tools/icarus.py              # discovery, version probes, compile/run arguments
    tools/simulation.py          # public origin-gated verification pipeline
  tests/
    unit/                        # offline unit and stub-tool tests
    integration/                 # real Icarus and CLI checks
    fixtures/adder4/              # pinned checker and nine controlled RTL candidates
  docs/
    PROJECT_SPEC.md, ARCHITECTURE.md, ROADMAP.md, DECISIONS.md, TEAM_ROLES.md
    reviews/                     # immutable review/handoff history and latest publication check
    milestones/M2_PLAN.md        # preserved proposed plan only; no M2 application code
  runs/                          # local generated evidence, ignored by Git
```

Implemented behavior includes the registered adder4 checker (256 input pairs), compiler/simulation diagnostics, explicit pass/fail/unknown outcomes, precompile policy rejection, model-origin blocking, timeouts, bounded stdout/stderr, POSIX process-group cleanup, before/after integrity hashes, and JSON artifacts. A successful compile alone cannot pass.

**Not implemented:** runtime LLM providers, prompts or natural-language RTL generation, one-shot generation orchestration, iterative repair, VerilogEval/RTLLM evaluation, pass@1/pass@k reporting, synthesis-based area/timing, Verilator execution, or FPGA deployment. The offline baseline needs no model API, GPU, training infrastructure, or distributed-computing system. The historical M2 plan has not been implemented and needs staffing adjustment for three students.

## Requirements

- Python 3.10 or newer (only 3.14.6 on macOS has been exercised so far).
- [Icarus Verilog](https://steveicarus.github.io/iverilog/) (`iverilog` and `vvp` on `PATH`). Verified with 13.0 (stable). On macOS: `brew install icarus-verilog`.
- Runtime code uses only the Python standard library. `pytest` is the only development dependency.
- Running M1 needs no API keys, network access, or GPU. Initial clone/dependency installation may need network access.

## Setup

For a new checkout:

```bash
git clone https://github.com/YCW701/llm-verilog-copilot.git
cd llm-verilog-copilot
```

From that repository root (or the existing `Capstone` workspace):

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

The editable install is required: in M1 the trusted fixture checkers are read from `tests/fixtures/` in this checkout.

`.gitattributes` marks `*.v` as `-text`, so Git never converts the line endings of Verilog files. The trusted checker is pinned by sha256, and a converted copy (e.g. a Windows `core.autocrlf=true` checkout) would fail the hash check. Generated `runs/` directories are not version-controlled.

## Usage

```bash
.venv/bin/python -m verilog_copilot verify \
    --rtl tests/fixtures/adder4/candidates/correct.v \
    --task adder4 \
    --output runs/my-first-adder4-run
```

The installed console script `.venv/bin/verilog-copilot` is equivalent. Expected output:

```text
task:      adder4
verdict:   pass
category:  none
screen:    ok
compile:   ok
simulate:  ok
message:   checker confirmed 256/256 vectors with 0 errors
artifacts: /…/runs/my-first-adder4-run
```

Options: `--compile-timeout SECONDS` (default 30), `--sim-timeout SECONDS` (default 10), `--max-log-bytes BYTES` (default 1 MiB per stream), and `--iverilog PATH` / `--vvp PATH` to choose explicit tool binaries.

`--output` must name a directory that does not exist yet. Existing runs are never overwritten.

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Functional pass confirmed by the trusted checker |
| 1 | Failed admission/verification: RTL policy violation, compile error, or checker-reported mismatch; inspect the category to distinguish these |
| 2 | Usage/configuration error: bad arguments, unknown task, missing RTL file, or output path already exists |
| 3 | Verdict unknown: simulation/compile timeout, inconclusive checker output, missing tool, a tool killed by a signal, log-capture failure, or infrastructure/integrity error |
| 130 / 143 / 129 | Interrupted by Ctrl-C (SIGINT) / SIGTERM / SIGHUP. Child process groups are killed; no `verification.json` is written, and the partial run directory is kept |

### Available fixture tasks

| Task | Interface | Trusted checker |
| --- | --- | --- |
| `adder4` | `module adder4(input [3:0] a, input [3:0] b, output [4:0] sum)`, `sum = a + b` | [tests/fixtures/adder4/tb_adder4.v](tests/fixtures/adder4/tb_adder4.v): exhaustive 256 vectors |

Sample candidates in [tests/fixtures/adder4/candidates/](tests/fixtures/adder4/candidates/):

| Candidate | Expected result |
| --- | --- |
| `correct.v` | `pass`, exit 0 |
| `wrong_behavior.v` | `fail` / `test_mismatch`, exit 1 |
| `syntax_error.v` | `fail` / `compile_error`; simulation `not_run`; exit 1 |
| `hang_silent.v` | `unknown` / `simulation_timeout`; use `--sim-timeout 2` to keep it short; exit 3 |
| `fake_pass.v` | `fail` / `candidate_policy_violation` (`$display`); never compiled; exit 1 |
| `early_finish.v` | `fail` / `candidate_policy_violation` (`$finish`); never compiled; exit 1 |
| `hang.v` | `fail` / `candidate_policy_violation` (`$display`); never compiled; exit 1 |
| `nonce_forgery.v` | `fail` / `candidate_policy_violation`; the review's nonce-aware forgery probe; exit 1 |
| `hierarchical_tamper.v` | `fail` / `candidate_policy_violation`; writes `tb_adder4.errors` through a hierarchical reference, with no system task; exit 1 |

The integration tests still run `fake_pass.v`, `early_finish.v`, and `hang.v` against the inner checker layer, with the screen skipped. That layer still classifies them as `test_mismatch`, `checker_inconclusive`, and `simulation_timeout` (with bounded logs). Those classifications predate the M1 correction.

## Run artifacts

Each run directory contains:

```text
<output>/
  manifest.json            # command, Python/platform, tool paths+versions, limits, trusted-file and source hashes
  verification.json        # schema "3": origin, screen result, stage statuses, process records (incl. capture_errors and version_probe), checker summary, verdict, category
  candidate.v              # private copy of the input; the input file itself is only read
  sim.vvp                  # compiled simulation (when compilation succeeds)
  compile.{stdout,stderr}.log
  simulation.{stdout,stderr}.log
  tool_versions/           # raw `iverilog -V` / `vvp -V` output
```

### How a verdict is decided

- **Execution gate.** `verify()` requires the caller to declare `origin`. `model_generated` returns `unknown` / `execution_policy_blocked` without copying or running anything. The CLI always declares `team_authored`. This is an API tripwire; it does not prove who wrote the file.
- **RTL admission screen** ([src/verilog_copilot/rtl.py](src/verilog_copilot/rtl.py)). It checks the private `candidate.v` copy, the exact bytes that get compiled. A violation is `fail` / `candidate_policy_violation`, and the candidate is not compiled. Rejected constructs:
  - system tasks/functions other than `$signed`, `$unsigned`, `$clog2`, and any other `$` (so `$` inside identifiers is not supported);
  - hierarchical references, e.g. `tb_adder4.errors`;
  - escaped identifiers;
  - `force`, `release`, `defparam` (also when they end a longer identifier such as `enforce`);
  - any compiler directive except `` `timescale ``.

  These rules define a **restricted supported subset** for M1. Some rejected constructs are legal, synthesizable Verilog (e.g. a local generate-scope reference, `` `default_nettype ``, `$` inside an identifier). A policy rejection is reported separately from a functional mismatch, and the team must revisit the subset before benchmark evaluation.

  The lexer follows Icarus 13.0's line handling, verified by probes:
  - a `//` comment ends at LF or CR (lone CR or CRLF); VT, FF, NEL and U+2028/U+2029 do not end it;
  - a string literal must close on its own line, so a raw CR/LF or a backslash line continuation inside a string is rejected;
  - a construct directly after a number (`#0$display`, `#1force`, `#256tb.errors`) is still detected.

  LF, CRLF and CR-only files are screened identically. The screen is lexical and conservative. It is **not** a sandbox and is not proven complete against every interference vector.
- **Stage status** (`not_run`, `ok`, `failed`, `timeout`, `tool_error`) is kept separate from the **verdict**: `pass`, `fail` (failed admission/verification; the category gives the reason), or `unknown`. Policy rejection does not establish a functional mismatch.
- A pass requires all of the following:
  - The trusted checker matches its pinned sha256, both before and after the run.
  - The candidate passes the admission screen.
  - Both `-V` version probes are recorded. A probe that cannot start, cannot be captured, times out, or is killed by a signal stops the run before compilation as `unknown` / `infrastructure_error`. A probe that prints no recognizable version is recorded with `tool_version: null` (and empty `capture_errors`) but does not block.
  - `iverilog` succeeds.
  - `vvp` exits 0 within its deadline, without being killed by a signal.
  - All stdout/stderr capture succeeds.
  - Stdout contains **exactly one** `CHECKER_RESULT` line, carrying the run's random nonce, the expected check count, and `errors=0`.
- Exit status alone never produces a pass, and neither do "PASS" banners printed by a candidate.
- A tool killed by a signal (other than our own timeout kill) is `unknown` / `infrastructure_error`, never a design verdict.
- A log that cannot be opened or written is recorded in `process.capture_errors` and makes the verdict `unknown` / `infrastructure_error`.

## Tests

```bash
.venv/bin/python -m pytest            # whole suite
.venv/bin/python -m pytest tests/unit # offline unit tests only; no Icarus needed
```

Integration tests (`tests/integration/`) run the real Icarus tools. If `iverilog`/`vvp` are not on `PATH`, they are reported as `SKIPPED: iverilog and/or vvp not found on PATH`, not as passes.

Publication validation and exact executed results are recorded in [M1_REVIEW_R4.md](docs/reviews/M1_REVIEW_R4.md). Tests cover controlled fixtures, not general correctness of arbitrary Verilog or future LLM behavior. No model or benchmark test was run for the baseline.

Executed on November 11, 2026, using the existing macOS / Python 3.14.6 / pytest 9.2.0 / Icarus 13.0 environment:

| Configuration | Result |
| --- | --- |
| Full suite with Icarus available | **287 passed** in 28.55 s |
| Icarus removed from the test process's PATH | **239 passed, 48 explicitly skipped** in 3.89 s |
| Full suite from a clean exported checkout, using the existing test interpreter | **287 passed** in 28.40 s |
| Separate public CLI run on `correct.v` | Exit 0; checker confirmed **256/256 vectors with zero errors**; schema-3 artifacts and matching source hashes inspected |

The commands used `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, and `--basetemp` under an external temporary directory. The no-Icarus run set `PATH=/usr/bin:/bin`. Setup installation from PyPI, other Python/platform versions, and live model/benchmark functionality were not tested by this publication check.

## Version control and local data

The original local `.gitignore` is preserved and combined with the GitHub starter ignore rules. Environment files, virtual environments, credentials/private keys, caches, generated simulator outputs and `runs/` are excluded. There are no required API keys in M1. Review the exact staged file list before committing; ignore rules cannot remove secrets that were already tracked. Do not commit real credentials even under an otherwise allowed filename.

Historical reviews and the existing M2 planning document are retained; their dated staffing assumptions describe earlier snapshots. [TEAM_ROLES.md](docs/TEAM_ROLES.md) describes the current three-student proposal. Codex and Claude share specifications and exclusive file ownership; technical approval does not adopt still-proposed architectural decisions on behalf of the team.

## Known limitations (M1)

- **Not a sandbox.** Timeouts, a minimal child environment, per-run directories, and the RTL screen are not OS isolation. They do not restrict filesystem, network, CPU, or memory use. An isolation policy must be adopted and validated before the **first execution of model-generated RTL**, in whichever milestone that happens (DECISIONS Q05). M2 mock responses may only be reviewed team fixtures.
- **Same-simulator trust.** The candidate runs in the same simulation as the checker.
  - The admission screen blocks the interference vectors shown so far: system-task forgery and hierarchical writes to checker state, including the line-ending and number-prefix variants found in review R2.
  - The nonce and single-result-line rule are a second layer, and they don't stop nonce-aware forgery on their own.
  - A nonce, a source hash, or OS isolation cannot by themselves prove which module printed a line.
  - The screen is not proven complete. Hostile RTL is outside M1's guarantees.
- **Process cleanup** kills the child's whole process group on normal exit, on timeout, and on SIGINT/SIGTERM/SIGHUP to the CLI. It cannot cover:
  - **SIGKILL to the harness**, which can't be intercepted; the simulator then keeps running until killed by hand.
  - **A descendant that leaves the group** (`setsid`), which can outlive the run. If it still holds a capture pipe, a `capture_errors` entry is recorded.
- **Bounded screen output.** At most 20 policy violations are listed per candidate, plus one "further violations not listed" entry.
- **Explicit tools with the same file name** (follow-up FU-M1-1, review M1-R3-N1). If `--iverilog` and `--vvp` point to two different executables with the same basename (e.g. two wrappers both named `tool`), the second version probe overwrites the first probe's raw log in `tool_versions/`. The default `iverilog`/`vvp` setup is unaffected.
- **Compiler diagnostics** can mention trusted checker paths and lines. Sanitize them before they are used as repair feedback (M3).
- **Platform.** Process-tree cleanup uses POSIX process groups. Windows is untested; WSL is suggested.
- **Toolchain.** Icarus 13.0 compatibility with any benchmark is unverified (DECISIONS Q04).
- **Manifest Git revision.** The unchanged M1 CLI currently writes `code_revision: null` even in a Git checkout. It records source hashes; use the Git commit/tag alongside them. Automatic Git revision capture is future work, not a claimed M1 feature.
