# Team Roles

Rutgers ECE Capstone, Group 62 — **four undergraduate ECE students**, academic year **2026–2027**. Faculty advisor: **Professor Hang Liu**. Updated November 11, 2026 from the team's corrected information.

The four roles below are **proposed technical responsibilities, not confirmed individual assignments**. Names, availability and final allocation remain open (DECISIONS Q01). Every student implements code, writes meaningful tests, maintains subsystem documentation, supplies reproducible evidence, and reviews another subsystem. M1 is implemented; later deliverables below remain planned. This staffing update does not assign or begin M2 implementation.

## Role 1 — AI Agent & Backend Engineering

**Implementation:** own Python orchestration, system integration, CLI/configuration, shared provider-neutral interfaces, run IDs, and experiment/artifact management infrastructure. Keep controller policy separate from provider SDKs, simulator commands, benchmark parsing and metric formulas. Integrate components against agreed contracts rather than becoming the sole implementer.

**Testing:** cover configuration validation, controller stage/stop behavior, exclusive artifact publication, linked metadata, cancellation and end-to-end CLI integration. Preserve the public M1 verification command and schema when adding future generation interfaces.

**Documentation and deliverables:** maintain architecture/interface examples, setup and CLI instructions, artifact schemas and integration handoffs. For M2, lead M2-A contracts and M2-E controller/CLI; review Role 4's generation evidence/storage slice. Own experiment execution/configuration infrastructure; Role 4 owns experimental methodology and metric interpretation.

**Cross-review:** review process integration and evidence provenance with Role 3, and storage/reproducibility with Role 4. Role 2 reviews Role 1's controller/request boundaries; Role 3 reviews verifier integration and cancellation.

## Role 2 — LLM Generation & Automated Repair

**Implementation:** own runtime LLM adapters, provider-neutral request/response normalization, offline mock/replay behavior, versioned prompts, natural-language-to-Verilog generation, deterministic response extraction, and bounded compiler/testbench-feedback repair. Keep transport retries separate from RTL repairs. Live integration depends on actual access and explicit budget/data policy; development-tool subscriptions do not establish API access.

**Testing:** cover adapter interchangeability, unsupported settings, normalized errors, bounded/truncated responses, extraction ambiguity, public-only prompts, repair lineage and all stop conditions. Verify that neither references nor trusted checker source leak through prompts or diagnostic feedback.

**Documentation and deliverables:** maintain provider capability/configuration instructions, prompt/extraction versions, feedback policy and failure analysis. For M2, lead M2-B prompt/mock and M2-F replay; review Role 3's bounded interface checks. Repair remains M3, not an M2 addition.

**Cross-review:** Role 3 reviews RTL/interface and feedback safety; Role 4 reviews replay/provenance and generation failure accounting. Review Role 1's orchestration to ensure no hidden extra inference, retries or model-selected execution commands.

## Role 3 — RTL Simulation & Verification

**Implementation:** own the bounded process runner, Icarus integration, trusted checker execution, compile/simulation error classification, integrity checks, and execution-safety enforcement. Evaluate a Verilator backend only if justified and separately assigned; lint alone is not verification. Check combinational/sequential behavior, clocks/resets, incomplete checker execution and false-pass attempts. Keep the model-generated RTL gate closed until an isolation policy is adopted and validated.

**Testing:** preserve and extend admitted/rejected RTL policy, real-tool, syntax/mismatch/timeout, bounded-log, process cleanup, capture-error and integrity regressions. Distinguish functional mismatch, policy rejection, infrastructure failure and unknown verdict. A lexical screen is not a sandbox or complete synthesizability checker.

**Documentation and deliverables:** maintain supported RTL subset, simulator versions/commands, execution limitations, checker rules and safety evidence. For M2, lead M2-C public task, reviewed generation fixture registry and supported interface checks; coordinate extraction semantics with Role 2. Preserve all existing trusted M1 fixtures and hash pins.

**Cross-review:** review Role 2's output checks/feedback and Role 4's benchmark qualification and synthesis RTL/tool assumptions. Role 1 reviews process orchestration/provenance; Role 4 checks checker qualification and result interpretation.

## Role 4 — Benchmarking, Evaluation & Synthesis

**Implementation:** own the pinned VerilogEval or RTLLM adapter, benchmark provenance, task qualification, pass@1/pass@k aggregation, one-shot versus repair comparisons, ablations and error analysis. Own later synthesis/library/constraint qualification and mapped area/static-timing reporting. Use the shared runner and artifact contracts instead of creating separate execution infrastructure.

**Testing:** validate metric formulas against known counts, separate dependent repairs from independent samples, retain coverage/failures, and qualify known-good/bad candidates jointly with Role 3. Cover candidate lineage, replay provenance, failure accounting, artifact links and missing synthesis metrics. Compare passing candidates and references under identical declared constraints and units.

**Documentation and deliverables:** maintain experiment protocols, provenance records, reproducible reports and synthesis setup/limitations. Propose coordination of the shared results table every two weeks starting at the baseline; its location and named custodian require team agreement. For M2, lead M2-D generation artifact/evidence implementation and tests under Role 1's schema contract; review M2-F replay. This is substantial implementation work without prematurely building M4 metrics or M5 synthesis. An early synthesis feasibility note requires a separate bounded assignment.

**Cross-review:** Role 1 reviews storage/report provenance and reproducibility; Role 3 reviews benchmark/checker and synthesis correctness. Review provider replay/failure accounting with Role 2.

## Integration boundaries and cross-review

| Boundary | Primary technical owner | Independent cross-review |
| --- | --- | --- |
| CLI, shared contracts, controller, artifact infrastructure | Role 1 | Role 2 for generation policy; Role 3 for verification integration |
| Providers, prompts, extraction, generation and repair policy | Role 2 | Role 3 for RTL/feedback integrity; Role 4 for replay/accounting |
| Runner, simulator, checker interpretation, RTL admission and isolation | Role 3 | Role 1 for lifecycle/integration; Role 4 for qualification evidence |
| Benchmark adapters, sampling/metrics, comparisons, synthesis/timing | Role 4 | Role 3 for RTL/tool correctness; Role 1 for provenance/reproduction |
| M2 generation artifact coordinator and evidence tests | Role 4 implements the agreed contract | Role 1 reviews schema/storage; Role 2 reviews replay compatibility |

Role 3 returns structured verification evidence; it does not decide campaign denominators. Role 4 owns numerical aggregation and reports incomplete coverage explicitly. Role 2 proposes sanitized feedback; Roles 3/4 check oracle integrity and evaluation leakage. Role 1 integrates these contracts without embedding provider SDKs or benchmark-specific rules in the controller.

These ownership areas are not permission for simultaneous edits. Before work, claim **every exact file** in [ROADMAP.md](ROADMAP.md#3-collaboration-and-file-ownership-ledger). Shared `models.py`, `rtl.py`, `cli.py`, fixture registries, manifests and documentation have one editor at a time; reviewers inspect read-only until a sequential handoff. The M2 slice plan refines temporary ownership without changing architectural boundaries. Each slice includes code, tests, documentation, evidence and released ownership.

Codex initially supports architecture, planning, technical review and independent test execution. Claude Code initially supports implementation. These are tool assignments, not student appointments or runtime provider choices. Either tool may take another role when explicitly assigned. Formal reviews and correction handoffs follow the shared permanent workflow; technical approval does not establish team adoption of architectural proposals or faculty checkpoint completion.

Students remain responsible for understanding and accepting outputs. No advisor meeting schedule, review obligation, approval, exact calendar deadline, API access or hardware availability is invented. Bring unresolved questions from [DECISIONS.md](DECISIONS.md) to the appropriate team/advisor discussion and record actual outcomes.
