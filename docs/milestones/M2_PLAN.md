# M2 Implementation Plan — Offline Providers and One-shot RTL Generation

Date: **November 8, 2026**  
Project: **An LLM Copilot for Verilog Design**, Rutgers ECE Capstone Group 62  
Author: **Codex — Software Architect and Technical Reviewer**  
Implementation baseline: **`7b4fbbea1d5b6a22863bf12b9053e378ef89743d` (`7b4fbbe`) on `main`**  
Status: **Proposed implementation plan; M2 is not implemented by this task.**

Planning revision: **November 11, 2026** — current team: **four undergraduate ECE students**, academic year **2026–2027**, faculty advisor **Professor Hang Liu**. Role labels and responsibilities below align with the current [TEAM_ROLES](../TEAM_ROLES.md) proposal; named assignments remain pending. Technical requirements, interfaces, security restrictions and M2-AC1–M2-AC12 are unchanged. The original date/baseline and inspection/handoff statements remain the November 8 planning record, not claims about this revision. The published M1 tag `m1-baseline` resolves to `e2e1066cebad8c12516818f813c08a71897f5d8e`; [R4](../reviews/M1_REVIEW_R4.md) records later publication verification.

## 1. Basis and intended result

This plan follows [ROADMAP](../ROADMAP.md), [PROJECT_SPEC](../PROJECT_SPEC.md), [ARCHITECTURE](../ARCHITECTURE.md), [DECISIONS](../DECISIONS.md), [TEAM_ROLES](../TEAM_ROLES.md), and the [M1 R3 technical review](../reviews/M1_REVIEW_R3.md). Root [AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md) govern ownership, handoffs, and independent review.

Local inspection confirmed a clean `main` at the supplied baseline commit before this planning task. M1 is technically approved with non-blocking issues. Its implementation choices M1-D1 through M1-D6 are still marked **proposed** in DECISIONS; the successful commit does not itself record team adoption. Some planning/status prose still says the repository is not initialized. The inspected Git state and the team's supplied baseline establish that it is now committed; this plan does not rewrite historical review reports or unrelated status text.

### Academic checkpoint relationship

M2 supports **Checkpoint 1 — FALL · WEEK 6: Baseline runs** and may continue into **Checkpoint 2 — FALL · FINALS: Core system**; the full mapping is in [ROADMAP](../ROADMAP.md#academic-checkpoints-and-milestone-mapping). Its approved mock/replay path cannot alone satisfy **“Data and an off-the-shelf model working end to end.”** Actual model access, public task/data qualification and adopted/validated execution isolation are additional gates before an end-to-end model baseline can be claimed. Do not expand this offline implementation assignment or lift the execution gate to meet a timeline. No checkpoint is claimed complete and no calendar dates are inferred.

M2 should deliver one small, reproducible path:

```text
Public hardware task
  -> versioned generation prompt
  -> selected offline provider (mock, then replay)
  -> saved raw response
  -> deterministic RTL extraction and interface checks
  -> candidate metadata and provenance admission
  -> existing public M1 verification for approved team fixtures only
  -> linked one-shot result and artifacts
```

The mock supplies canned responses. It does not demonstrate an LLM's hardware-design ability. All examples must be labeled offline/mock or replay, with no model-accuracy, token-cost, or benchmark claims. One-shot means **one provider invocation, one sample, attempt index 0, zero repairs, and zero transport retries** in M2.

## 2. Scope and non-goals

### Required M2 scope

- Public `TaskSpec`, provider-neutral request/response contracts, and explicit provider capabilities.
- Deterministic mock provider with reviewed synthetic response cases; no credentials or network.
- A versioned natural-language-to-RTL generation prompt using public task/interface information only.
- Deterministic raw/fenced response extraction and a documented small interface-validation subset.
- Stable candidate/sample/attempt identifiers, origin tracking, hashes, and generation-stage outcomes.
- A one-shot controller and additive CLI entry point integrated with public M1 interfaces.
- Machine-readable artifacts linking request, response, candidate, stage outcomes, and M1 verification evidence.
- Focused offline tests plus real-Icarus integration on reviewed fixture responses.
- A second interchangeable offline adapter, proposed as replay, to satisfy the roadmap's two-adapter contract-test target without assuming live API access.

The proposed mock-plus-replay interpretation needs team confirmation (M2-P1 below). A mock alone is the first implementation slice, not the complete two-adapter exit gate. If the team wants a real API adapter instead, record that scope decision and its access/budget dependencies before implementation; do not silently waive the roadmap target.

### Explicitly deferred

Repair prompting/loops and feedback consumption (M3); benchmark import and pass@k campaigns (M4); synthesis/STA implementation (M5); paid/API/local-GPU inference; training; a web UI; frameworks; databases; concurrent experiment workers; automatic resume; and arbitrary plugin loading. Do not add unused skeletons for these features.

Q05 isolation remains unresolved. **Executing actual model-generated RTL is outside M2's permitted offline scope.** The existing execution gate must remain intact. A future live generation-only demonstration would need its own access authorization and must keep its candidates model-generated and unexecuted.

## 3. Preserve the approved M1 boundary

The committed implementation, rather than the architecture's earlier semantic shorthand, defines the integration contract:

```python
verify(candidate: Path, bundle: VerificationBundle, limits: SimulationLimits,
       run_dir: Path, tools: IcarusTools, *, origin: CandidateOrigin
) -> VerificationResult
```

`run_dir` must be a newly created **empty** verifier directory. Public `verify()` copies the candidate to its own `candidate.v`, screens those exact bytes, records version probes, compiles and simulates, and returns evidence. M2 must not pre-create its candidate or JSON files inside that directory. Do not call `_verify_impl` or pass `screen_rtl=False` from application code.

Reuse `create_run_dir`, `write_json_exclusive`, `sha256_file`, `find_tools`, `SimulationLimits`, `CandidateOrigin`, and `VerificationResult`. Keep M1's artifact schema **3**, enum values, `verify` CLI behavior, checker pin, admission policy, process execution, signals, capture-error propagation, and outcome classifications unchanged unless a separately assigned change is reviewed.

Future M2 implementation may add records to `models.py`, add a CLI subcommand, and add extraction/interface helpers to `rtl.py` under exact-file ownership. Those are future additive integration tasks, not changes made by this plan. No simulator rewrite or M1 refactoring is needed. Prefer new modules for generation configuration/controller/providers and artifact orchestration; reuse the existing storage primitives.

### Existing non-blocking follow-ups

- **FU-M1-1 / M1-R3-N1:** same-basename explicit tool paths can overwrite version-probe logs. Keep M2 integration on qualified tools with distinct basenames. Fix under a separate claim before relying on same-basename wrappers; do not silently fold a tool-runner change into provider work.
- **FU-M1-2 / M1-R3-N2:** the `Verdict` docstring needs to distinguish policy rejection from functional mismatch. Assign the small clarification alongside the next owned result-contract update, or explicitly defer it. It does not require changing enums or exit codes.
- M1's CLI manifest still sets `code_revision=None`. New M2 manifests must record the current Git revision/dirty state and source hashes rather than copying that obsolete assumption. Updating M1's own manifest behavior is separate work.

## 4. Public task and mock data

Start with the existing `adder4` task: top module `adder4`; unsigned inputs `a[3:0]` and `b[3:0]`; unsigned output `sum[4:0]`; combinational unsigned addition with carry; Verilog-2005; no clock/reset or parameters. Store this as public task data in a new `benchmarks/local_tasks.py` registry, independently of the private verification bundle. Do not derive provider input by serializing `VerificationBundle`.

Use synthetic response data under a new `tests/fixtures/generation/` directory. Begin with correct raw RTL, correct fenced RTL, wrong behavior, syntax error with a valid header, wrong interface, empty output, ambiguous multiple code blocks, a policy violation, and a normalized provider-error case. Reuse/read the existing candidate fixtures where appropriate; never edit the existing checker or fixtures to satisfy new expectations.

A closed mock-case registry should record case ID, task ID, raw response source/hash, expected extracted candidate hash when applicable, and reviewed-fixture provenance. It is trusted development configuration, not fields a response can invent. Exact candidate bytes must be verified against the approved fixture record before being admitted as team-authored. Replacing a response file or changing extraction output must not silently preserve that trust.

## 5. Proposed data contracts

Use standard-library dataclasses/enums/Protocols. Freeze field names and serialized examples in M2-A before independent module work. New top-level generation documents should have `generation_schema_version="1"`; embedded M1 records retain their own `schema_version="3"`. Do not change M1's global schema merely to add a separate generation envelope.

| Record | Required fields and rules |
| --- | --- |
| `PortSpec` | Name, direction, signedness, explicit packed range or scalar, and width; preserve range orientation rather than comparing width alone. |
| `TaskSpec` | Task ID/revision, public behavior, top module, ordered ports, language profile, parameter/clock/reset declarations (explicitly empty/none for adder4), public constraints, task-content hash. No checker/reference paths or source. |
| `ProviderCapabilities` | Adapter ID/version, offline/live kind, supported settings, supported output limits, and provenance policy. Unsupported settings are rejected, never silently dropped. |
| `GenerationConfig` | Provider/model label, mock case or replay source, output mode, bounded prompt/response/candidate sizes, output directory, explicit one-call/no-retry/no-repair policy, and M1 simulation limits. No credentials. |
| `GenerationRequest` | Request ID, task ID/hash, prompt text/version/hash, requested output limits, accepted sampling settings, and request fingerprint. Provider-visible content is public only; no filesystem/tool execution handles. |
| `GenerationResponse` | Adapter identity and model label, raw text or structured service error, finish reason, latency, provider request ID when available, optional usage, and source-record reference for replay. Mock token usage/cost is null unless explicitly simulated and labeled as such. |
| `ExtractionResult` | Status, extraction method/version, exact response byte span, candidate bytes or no candidate, candidate hash, and bounded diagnostics. Raw and extracted text are separate. |
| `InterfaceCheck` | `ok`, `mismatch`, `unsupported`, or `not_run`; expected/observed top and port declarations; bounded diagnostics. Neither `ok` nor lexical admission implies functional correctness or synthesizability. |
| `Candidate` | Candidate ID; run/task/sample/trajectory IDs; `attempt_index=0`; `parent_candidate_id=null`; request/response references; candidate path/hash if extraction succeeded; extraction/interface statuses; separately resolved origin and reviewed-fixture evidence. IDs identify attempts; hashes identify bytes. |
| `OneShotResult` | Stage outcomes, candidate or null, terminal reason, overall verdict, generation failure category when applicable, optional M1 verification record/path, call/attempt counts, durations, and artifact references. Preserve M1's category unchanged when verification ran. |

Allocate run/sample/trajectory/request IDs before invoking the provider. A service failure still gets an attempt/result record, even when there is no candidate. A response with extraction failure may have candidate metadata with null path/hash; it must not fabricate an executable RTL file. Identical bytes from different requests retain distinct IDs. Record UTC timestamps and measured durations, without making them part of deterministic content hashes.

Request fingerprints should use a versioned, canonical serialization of public task identity, exact prompt/version, model label, and supported generation settings/output limits. Exclude per-run IDs, timestamps, and local artifact paths. Define this once for both adapters; it is a reproducibility key, not proof of authorship.

## 6. Module interfaces and responsibilities

These are proposed interfaces, not currently available features. Keep dependencies directed toward neutral models and existing M1 contracts.

| Module | Proposed interface / responsibility | Boundary |
| --- | --- | --- |
| `models.py` | Add the generation records above and `GENERATION_SCHEMA_VERSION`. | Preserve existing M1 records and serialization. No I/O, provider SDK, or process launch. |
| `config.py` | Validate `GenerationConfig`, supported provider settings, mode, and bounded limits before a call. | No environment-derived provider selection or implicit live fallback. |
| `benchmarks/local_tasks.py` | `get_task_spec(task_id) -> TaskSpec`; only reviewed public task data. | Private `get_bundle()` remains in the existing fixture adapter. |
| `providers/base.py` | `Provider` Protocol with `capabilities` and `generate(request) -> GenerationResponse`; normalized provider-error contract. | No simulator, checker bundle, shell access, or verdict decisions. |
| `providers/mock.py` | `MockProvider(case_id, trusted_case_registry)` returns one bounded canned response/error. | Case selection is configuration; no execution of response text and no arbitrary import/plugin path. |
| `providers/replay.py` | `ReplayProvider(record_source)` verifies a recorded response/fingerprint and returns it through the same contract. | No inference; distinguish replay transport from original response provenance. Unknown/untrusted provenance never becomes team-authored. |
| `providers/__init__.py` | Small explicit `mock`/`replay` factory/registry. | No framework, auto-discovery, network initialization, or optional SDK import on startup. |
| `prompts.py` | `build_generation_request(task, config, ids) -> GenerationRequest`; versioned public-only template. | Do not send checker source, golden RTL, expected vectors, private paths, or raw verifier diagnostics. |
| `rtl.py` | Add pure `extract_rtl(response) -> ExtractionResult` and `validate_interface(candidate_bytes, task) -> InterfaceCheck`. | Preserve the approved `screen_candidate_rtl` behavior; no repair or semantic rewriting. |
| `generation_storage.py` | New small generation artifact coordinator using existing `storage.py` primitives; manifests, relative paths, IDs, exclusive writes. | No database, verdict selection, or shell invocation. |
| `controller.py` | `run_one_shot(task, provider, config, verification_context) -> OneShotResult`. | One provider call; provenance admission; public verifier only. No repair policy, compiler flags, or provider SDK details. |
| `cli.py` | Add `generate`; validate arguments, construct dependencies, report result/paths and meaningful exit code. | Keep `verify` compatible; no duplicated verification logic or testbench parsing. |

`verification_context` is a private application dependency holding the fixed bundle, discovered tools, and limits. It must never become part of a provider request. If an interface helper needs lexical tokens, implement only the bounded supported subset with comment/string handling consistent with the approved scanner; do not introduce a second permissive screen or a regex that mistakes comments for module declarations.

### Provider interchangeability and replay

Run the same capability/error/request-response contract tests against mock and replay, and switch them through configuration without changing the controller. Replay must reject request-fingerprint mismatch, malformed/schema-incompatible records, oversized content, and invalid hashes with normalized provider errors. No retries occur in M2.

A replay must retain original provider identity, response hash, source-run reference, and original provenance separately from the new replay event/request ID. A recorded model response remains `MODEL_GENERATED`, even if the transport is local or its bytes equal a reviewed fixture. A user-editable `origin` field in JSON cannot grant trusted execution. Only replay of an independently recognized, registered reviewed mock fixture can qualify for the existing team-authored path. All other replay content is generation-only or execution-blocked.

## 7. Extraction and interface policy

Propose these initial supported response forms:

1. Raw UTF-8 containing a complete single-module design, with whitespace/comments and a permitted timescale directive.
2. Exactly one fenced block tagged `verilog` or untagged; permitted surrounding prose is preserved in the raw response but excluded by recorded byte offsets.

Reject empty output, malformed/unclosed fences, multiple candidate blocks, unsupported encoding/NUL, unsupported fence languages, and output beyond the accepted limit. Do not pick the first or last module/block to hide ambiguity. No fixes such as renaming modules, inserting ports/semicolons, adding missing `endmodule`, stripping dangerous constructs, or silently changing line endings. Extraction removes only the documented envelope; record the resulting exact UTF-8 bytes and hash. A length-truncated provider response must not be compiled as if complete.

The interface checker should initially support one unparameterized module with explicit constant packed ranges, simple ANSI declarations and a bounded non-ANSI form. Check top name, exact port set/directions/ranges/signedness, duplicates, missing/extra ports, and conflicting declarations against `TaskSpec`. If non-ANSI support would materially enlarge the first slice, decide that before coding and document an ANSI-only subset; do not claim unsupported declarations passed validation. Parameters, unresolved width expressions, multiple/helper modules, and broader SystemVerilog are `unsupported` for this initial task profile, not proof of a functional mismatch.

Keep outcome distinctions explicit: a definite declared-port mismatch is `interface_mismatch`; an unhandled legal form is `unsupported_interface`; malformed/ambiguous response extraction is `extraction_error`. Generation-stage categories live in the generation envelope rather than being disguised as compiler errors. A valid header with a body syntax error should still reach M1 and produce its existing `compile_error`, preserving useful end-to-end compiler evidence.

## 8. One-shot behavior and execution restrictions

1. Validate public task, selected built-in provider, capabilities, mode and limits. Resolve private task verification context separately. Create a collision-refusing run directory and immutable initial manifest.
2. Save the public task/config snapshots and request. Invoke the provider **once**. Save its bounded raw response or normalized error before taking another stage action.
3. On successful, complete response, extract candidate bytes and record the extraction evidence. Perform supported interface checks and the existing lexical admission check without rewriting the candidate.
4. Resolve candidate origin from trusted application configuration plus verified fixture provenance, never from the response's claim, provider name alone, or content hash alone. Only approved mock-fixture cases whose extracted bytes match the reviewed record qualify as team-authored. Tampering/missing fixture evidence stops verification.
5. In generation-only mode, save the candidate and statuses, set verification to `not_run`, and stop. Successful generation is not a functional pass; overall functional verdict is `unknown` with terminal reason `generation_only`.
6. In verification mode, pass admitted reviewed fixture output to public M1 `verify()` with `TEAM_AUTHORED` in a separate empty directory. For actual model-origin content, preserve `MODEL_GENERATED` and obtain/record the existing execution-blocked result without tool execution. For content claiming team origin but lacking reviewed-fixture evidence, stop in the controller as `provenance_blocked` without calling the verifier or fabricating a M1 result. Do not route either case through the old CLI's implicit team-authored assumption.
7. Save the terminal generation result and a final manifest/result link. Stop on every pass/failure/unknown outcome. No second generation, repair, tool-triggered retry, or automatic resume.

Suggested terminal categories include `provider_error`, `response_truncated`, `response_too_large`, `extraction_error`, `interface_mismatch`, `unsupported_interface`, `provenance_blocked`, `generation_only`, and the preserved M1 verification category. Provider/service failures and infrastructure conditions are `unknown`; definite rejected response/interface/policy outcomes may be `fail`, explicitly distinguished from `test_mismatch`. Exact mappings must be frozen in M2-A, not inferred from a nonzero exit alone.

Retain exit codes 0/1/2/3 and existing cancellation codes. Propose: 0 only for a verifier-confirmed functional pass; 1 for a definite response/interface/admission/design failure; 2 for invalid CLI/configuration; 3 for unknown, generation-only, service failure or execution-blocked. The CLI must separately print successful generation stages when exit 3 reflects unverified RTL. This choice avoids silently treating generated-but-untested code as a functional pass; confirm it before CLI implementation.

### Proposed CLI targets

These commands are planning examples, not currently runnable:

```bash
.venv/bin/python -m verilog_copilot generate \
  --task adder4 --provider mock --case raw-correct \
  --mode verify --output runs/m2-mock-correct

.venv/bin/python -m verilog_copilot generate \
  --task adder4 --provider replay --record <recorded-response> \
  --mode generate-only --output runs/m2-replay
```

There must be no `--unsafe`, `--skip-screen`, CLI-controlled trusted-origin override, arbitrary checker path, model-chosen output filename, or dynamic provider-import option. Providers and model labels are runtime application configuration, separate from Codex/Claude development-tool assignments.

## 9. Artifacts and metadata

Proposed one-task/one-sample layout, following the architecture without implementing a campaign engine:

```text
runs/<run_id>/
  manifest.json                         # immutable initial config, revision, versions/hashes
  public_task.json
  tasks/<task_id>/samples/<sample_id>/
    attempts/000/
      request.json
      response.json                     # raw response metadata/text or normalized service error
      candidate.json                    # IDs, origin, hashes, extraction/interface evidence
      candidate.v                       # only if extraction succeeded
      verification/                     # created empty for the existing M1 verifier
        candidate.v                     # M1's independent byte-exact copy
        tool_versions/...
        compile.*.log
        simulation.*.log
        verification.json               # saved from returned M1 schema-3 record
    trajectory.json                     # one initial attempt, parent null, no repairs
  result.json                           # final outcome + manifest hash; no overwrite of manifest
```

This is a single-run structure, not evidence that batch evaluation exists. Reuse exclusive/atomic JSON publication; add equivalent exclusive text/byte publication only where needed. Never overwrite initial manifests or previous attempts to make a final status appear complete. Preserve partial artifacts on interruption and identify incomplete runs without fabricating a final verdict. No automatic resume is required.

The manifest should record the full current Git revision and dirty state (using fixed read-only argument lists through the runner, or a documented validated snapshot mechanism), package/Python/platform identity, baseline `7b4fbbe`, source hashes, generation schema, public task/prompt versions/hashes, provider and case/replay identity, effective settings/limits, and provenance policy. Read-only Git queries must not run per-user hooks or expose remote credentials. If revision is unavailable, record null plus the reason and source hashes; do not falsely label every later run as the original baseline. Actual verifier/tool versions and trusted asset hashes belong in its linked evidence and final result. Store artifact references relative to the run root where practical, with traversal checks.

Use unique IDs; a content hash cannot replace candidate/sample/attempt IDs. A replay creates new event IDs while retaining the source reference. Record one invocation for mock/replay, zero live inference calls, one initial sample, and zero repairs. Missing usage is null, not guessed or simulated model telemetry. Do not compute pass@1/pass@k from canned cases or report a mock run as a benchmark result.

## 10. Limits and security requirements

- **Preserve the generated-code gate.** Local storage, replay, a matching hash, or a mock adapter name does not turn actual model output into team-authored RTL. User-supplied record metadata cannot authorize execution.
- **Protect verification material.** Providers receive only `TaskSpec` and prompts. Checkers, reference implementations, private paths and vectors never enter requests. Test this boundary with sentinel private fields; preserve pinned checker bytes.
- **Keep the M1 screen authoritative.** Do not normalize CR/CRLF in candidate files or bypass admission in the controller. Preserve the existing CR, string-continuation, number-prefix, hierarchy, and bounded-output regression coverage.
- **Bound local inputs before loading.** Proposed starting limits: public task/prompt 64 KiB each; raw response/candidate 1 MiB each; diagnostics at most 20 entries plus truncation marker; one request, no retries, no repairs. Reject oversize content without silently extracting a truncated candidate. Confirm numbers in M2-A.
- **Reuse tool limits.** Initial proposal retains M1 defaults: 30 s compilation, 10 s simulation, 1 MiB per captured stream, 1 MiB candidate, and existing fixed version-probe/cleanup limits. Account for probes and cleanup in run-level accounting rather than calling compilation+simulation time the entire run duration.
- **Be precise about aggregate bounds.** Fixed one-shot counts plus bounded built-in local providers/tool stages give finite planned work. Validate an aggregate artifact allowance before writes and audit produced files. M1 does not impose a hard quota on compiler-produced `sim.vvp`, and an in-process elapsed-time check cannot interrupt arbitrary Python. Do not advertise hard disk/whole-run isolation or arbitrary-provider timeouts. Execution stays on prequalified small fixtures; enforce transport deadlines when a real provider is separately introduced. No unbounded plugin/callback execution is supported.
- **Treat all text as data.** No `eval`, `exec`, shell interpolation, dynamic imports from responses, model tool calls, file-path commands, or extra simulator flags. IDs/path segments are harness-generated or validated; reject traversal and symlink escapes from allowed fixture/replay/artifact roots.
- **Preserve process/security behavior.** No new subprocess launch outside `tools/process.py`; keep the minimal child environment and cancellation cleanup. There are no keys or SDKs to discover, require, or log in offline M2.
- **Avoid scope inflation.** No containers/services, global toolchain changes, automatic dependency installation, or full parser/security framework for this milestone. The existing lexical subset is a policy, not proof of security or synthesis quality.

## 11. Implementation slices and four-person task plan

Estimate: **roughly 1–2 working weeks**, subject to actual part-time availability and review turnaround, not a course/faculty deadline. The team must assign names (Q01). File ownership is per task, not a permanent right to edit another contributor's file. No agent has an implementation claim from this plan.

| Slice | Primary student role / reviewer | Proposed deliverable and files | Gate / indicative effort |
| --- | --- | --- | --- |
| **M2-A — Contracts and decisions** | Role 1 AI Agent & Backend Engineering / Role 2 | Freeze records/config/error mappings, public task shape, provenance and artifact contracts; additive `models.py`, new `config.py`; `tests/unit/test_generation_models.py`; adopted decisions and schema examples. | Resolve M2-P1–P5 below; 0.5–1 day. Complete shared-model edits before other implementations depend on them. |
| **M2-B — Prompt and mock** | Role 2 LLM Generation & Automated Repair / Role 3 | `providers/__init__.py`, `providers/base.py`, `providers/mock.py`, `prompts.py`; `tests/unit/test_providers.py`, `tests/unit/test_prompts.py`. | M2-A and frozen fixture registry supplied by Role 3; 1–2 days. No simulator call in provider code. |
| **M2-C — Public task, fixtures, RTL output checks** | Role 3 RTL Simulation & Verification / Role 2 | `benchmarks/local_tasks.py`; new generation fixture/task/case files; additive `rtl.py` extraction/interface helpers; `tests/unit/test_rtl_generation.py`. | M2-A; 1–2 days. Preserve all existing RTL screen tests and original fixtures. |
| **M2-D — Candidate artifacts and replayable evidence** | Role 4 Benchmarking, Evaluation & Synthesis / Role 1 | `generation_storage.py`; `tests/unit/test_generation_storage.py`; artifact/schema examples and lineage/provenance assertions. | M2-A; 1–2 days. No benchmark metric or synthesis implementation. |
| **M2-E — Controller and CLI integration** | Role 1 AI Agent & Backend Engineering / Role 3 | `controller.py`, additive `cli.py`; `tests/unit/test_controller.py`, `tests/integration/test_generate_cli.py`; README examples and status updates. | M2-B/C/D; 1–2 days. Single provider call and public M1 verification only. |
| **M2-F — Replay adapter and substitution checks** | Role 2 LLM Generation & Automated Repair / Role 4 | `providers/replay.py`; append contract cases to owned `test_providers.py`; integration cases added by the current owner of `test_generate_cli.py` after handoff. | M2-D and frozen request fingerprint; 0.5–1 day. No ownership overlap with M2-E tests. |
| **M2-G — Acceptance and independent review** | All roles; Codex independently reviews | Execute acceptance matrix; save implementation handoff and independent review under `docs/reviews/`; update review history and release ledger claims. | Prior slices; allow 1–2 days for evidence/review and bounded corrections. |

Every slice includes implementation, behavior tests, subsystem documentation and a released-ownership handoff. Role 1 leads contract/integration documentation and controller tests; Role 2 maintains provider/prompt examples and adapter tests; Role 3 documents the interface/admission subset and supplies safety/real-Icarus evidence; Role 4 implements generation artifact storage against Role 1's agreed contract, documents metadata/replay examples and checks lineage/failure accounting. This delegated M2-D work does not transfer architectural ownership of shared storage contracts.

Role 4 also owns the one-shot metadata/replay invariants and failure-accounting tests, so its engineering work is substantial without prematurely implementing M4 metrics. A synthesis/library feasibility note may be scoped separately as the roadmap suggests; it must not delay or expand the M2 provider deliverable.

### Ownership sequencing

The paths above are planning assignments, not sufficient ledger claims. Before each slice, enumerate **every exact file**, including package `__init__.py`, individual JSON/text fixtures, docs, and tests; replace aggregate descriptions with actual paths. Role 3 owns creating/changing shared generation fixture data and hands off its frozen registry to Roles 2/4. Role 1 serializes `models.py`, `cli.py`, shared manifests/contracts and status-doc edits. Role 2 owns `test_providers.py`; cross-role additions use a sequential handoff. `rtl.py` has one editor even though it contains both old screening and new helpers.

Human work may proceed on disjoint paths after interfaces freeze. Codex initially plans/reviews/tests, Claude Code initially implements only explicitly assigned slices. Do not launch multiple editing agents or let tools edit overlapping files merely because tasks are listed in parallel. Read-only review can overlap; fixes require ownership transfer. Claim ROADMAP/DECISIONS edits before changing them; preserve historical review reports and existing local runs.

## 12. Acceptance and test matrix

These checks are **planned**, not executed by this documentation task. Require behavior/evidence tests, not tests that merely mirror implementation. The approved baseline's last independent suite was 287 passed with Icarus and 239 passed / 48 skips without it; rerun it during implementation and report actual counts after adding M2 tests.

| ID | Acceptance criterion | Required verification evidence |
| --- | --- | --- |
| **M2-AC1** | One-shot mock path works offline from public natural language/interface to saved RTL. | Correct raw and fenced cases produce the intended candidate; no credentials, network, SDK, or GPU initialization; exactly one provider invocation, zero retries/repairs. |
| **M2-AC2** | Public/private boundaries are enforced. | A spy provider sees only allowed public request fields. A private checker-source/path sentinel never appears in request/prompt artifacts. Bundle/reference data is not serialized into provider requests. |
| **M2-AC3** | Mock and replay are interchangeable through one contract. | Same shared tests cover capabilities, successful response, normalized errors, unsupported settings, response bounds and deterministic content. Controller is unchanged when selecting replay; mismatched/corrupt replay records fail clearly. No live-provider claim is made. |
| **M2-AC4** | Extraction is deterministic, bounded and transparent. | Raw/single-fenced outputs; original response/span/hash retained; empty/malformed/multiple blocks and truncation cannot compile; CR/CRLF/LF byte handling explicit; no silent repair or module selection. |
| **M2-AC5** | Interface checks are useful without overstating parser coverage. | Correct ANSI and the adopted non-ANSI forms accepted; wrong top, missing/extra/duplicate ports, direction/range/signedness mismatches rejected; unsupported parameterized forms labeled; valid header/body-syntax error still reaches M1 compile failure. |
| **M2-AC6** | Candidate IDs, lineage and schema links are correct. | Distinct request/sample/candidate IDs for repeated identical bytes; same byte hash; attempt 0, parent null; references resolve; M1 schema remains 3 inside generation schema 1; mock usage/cost labeled/null. |
| **M2-AC7** | Reviewed mock candidates integrate with real M1 verification. | Correct candidate passes all 256 vectors; wrong behavior yields `test_mismatch`; syntax error yields `compile_error` with no simulation; policy-violating fixture never compiles; admitted silent hang yields timeout/unknown. Preserve returned categories and full evidence. |
| **M2-AC8** | No source of unreviewed/model content gains trusted execution. | Declared model origin, arbitrary replay records claiming team origin, forged mock IDs/hashes, changed fixture bytes, and model text equal to a known fixture cannot bypass provenance/gate checks. Tool-call spy confirms no execution. A valid registered reviewed mock case still verifies. |
| **M2-AC9** | Failure and cancellation do not look like correctness. | Provider error/oversize/truncated output and unsupported interface stop appropriately; missing Icarus yields infrastructure/unknown; generation-only has successful generation stages but no functional pass; controller never retries; cancellation retains partial artifacts and existing signal semantics. |
| **M2-AC10** | Artifacts preserve evidence and refuse collision. | Rerun to an existing output leaves it unchanged; prompt/raw response/candidate/execution copies have expected hashes; path traversal/symlink escapes rejected; source/checker unchanged; current revision/dirty state/source hashes recorded; incomplete artifacts not reported as a completed pass. |
| **M2-AC11** | M1 compatibility and execution restrictions remain intact. | Existing baseline suite passes with real Icarus; no-Icarus suite reports explicit skips; original public `verify` command and origin gate work; CR/continuation/number-prefix/capture-error/cleanup regressions remain effective. No test-only bypass is imported by production generation code. |
| **M2-AC12** | Handoff and reproducibility are reviewable. | README has executed offline examples, exact commands/results, known limitations and artifact locations. Claude saves a unique `M2_HANDOFF_R1.md` (or next unused name); Codex independently executes checks, saves `M2_REVIEW_R1.md`, updates review index, and gives a verdict. Proposed team decisions are not silently marked confirmed. |

### Suggested implementation validation commands

After relevant files exist, use the existing environment and external temporary directories. These are targets; they have not run for M2:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp <new-temporary-directory>

PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest -p no:cacheprovider \
  --basetemp <different-new-temporary-directory>
```

Use focused tests per slice before the final full suite. Exercise the public CLI and independent resulting JSON, not only mocked controller calls. Do not pin success to a historical test count or weaken assertions to preserve it. Live API and benchmark checks remain unexecuted/deferred, explicitly labeled.

## 13. Unresolved decisions and gates

The defaults above make the plan concrete; they are not recorded team decisions. Resolve the following before the affected implementation slice and record the outcome/authority in DECISIONS. No API key, GPU, simulator installation, or benchmark download is needed to resolve the offline design.

| ID | Decision needed | Recommendation | Owner / gate |
| --- | --- | --- | --- |
| **M2-P1** | What meets the roadmap's two-provider-adapter gate? | Mock plus local replay for offline M2; live API adapter deferred. Confirm this interpretation rather than silently calling one mock a complete milestone. | Team + Role 2, before M2-A/B. |
| **M2-P2** | Exact provenance/admission rule for reviewed mock and replay data. | Closed reviewed-case registry plus exact extracted-byte hashes and retained source provenance. Never trust an adapter name or JSON origin claim alone; actual model output stays model-generated. | Roles 1/2/3 + team, before any M2 verification integration. |
| **M2-P3** | Initial extraction/interface subset and outcomes. | Raw/single-fenced Verilog; one unparameterized module with explicit ranges; adopt ANSI/non-ANSI scope and unsupported classifications before implementation. Preserve M1 admission restrictions. | Roles 2/3, before M2-C. |
| **M2-P4** | Generation schema, fingerprint, terminal categories and CLI generation-only exit behavior. | Separate generation schema 1 embedding M1 schema 3; stable IDs; explicit unknown/unverified outcomes, with 0 reserved for functional pass. | Roles 1/4 + team, before M2-A/E. |
| **M2-P5** | Concrete byte/artifact/stage budgets and optional settings. | Use the bounded offline defaults in section 10, one call, zero retries/repairs; document limits honestly. No implicit temperature/seed support or fake token telemetry. | Roles 1/2/3/4, before M2-A. |
| **Existing M1-D1–D6** | Team adoption is still not recorded. | Record accept/modify/defer with dates/authority for the inherited tooling, verdict, fixture, subset, origin-gate and schema choices relevant to M2; technical approval/commit alone is not adoption. | Team, before freezing dependent M2 contracts. |
| **Q01** | Named owners and actual availability. | Assign four students to the roles/slices and confirm file ownership sequencing. Estimates above are not deadlines. | Team, before implementation assignments. |
| **Q02** | Runtime provider access/budget/data policy. | Does not block offline mock/replay. Resolve only before separately authorized live calls; development subscriptions do not imply API access. | Role 2 + team, before live-provider scope. |
| **Q05** | Isolation for actual generated RTL. | Keep existing gate closed. Must be adopted/validated before first execution, regardless of milestone. It does not block approved mock-fixture execution. | Roles 1/3 + team, before lifting gate. |
| **Q03/Q04/Q07/Q08/Q09** | Benchmark revision/toolchain, experiment sampling/feedback, and synthesis library/constraints. | Remain future gates. Do not delay the offline provider path or invent benchmark/numerical results. Scope an early synthesis feasibility note separately if useful. | Appropriate subsystem owners before M3–M6 activities. |

## 14. First assignment and completion handoff

Recommended first Claude Code assignment: **M2-A, then the smallest M2-B mock slice**, after the relevant decisions/ownership are recorded. Produce neutral records, public task/prompt/request examples, a deterministic mock adapter and offline contract tests; do not begin a repair loop or a live API integration. Review those contracts before parallel module work.

M2 is complete only after M2-AC1 through M2-AC12 have executed evidence, both proposed offline adapters satisfy the agreed contract gate, the public one-shot fixture path works, the generated-RTL gate remains closed, and Codex saves an independent technical review. Remaining limitations and any team-approved scope change must be explicit. A canned mock demonstration is engineering integration evidence, not completion of capstone efficacy evaluation.

### Original planning-task record (November 8, 2026)

This task created the plan and its ownership entry only. It did not implement M2, modify M1 application code, install dependencies, execute new application tests, alter the existing decisions, make a Git commit, or push anything to GitHub.
