# Project Specification

Project: **An LLM Copilot for Verilog Design**  
Rutgers ECE Capstone, Group 62 — three undergraduate ECE students, academic year 2026–2027<br>
Faculty advisor: Professor Hang Liu  
Planning baseline: November 8, 2026; current team information: November 11, 2026

## 1. Purpose and status

Build a reproducible system that turns natural-language hardware specifications into Verilog RTL, evaluates the RTL with simulation, and uses diagnostic feedback to repair failed designs. Compare the benefit and cost of repair against independent one-shot generation.

This is a planning baseline, not an implemented system or a statement of faculty requirements beyond the information supplied by the team. No advisor approval, course deadline, numerical performance target, API access, or GPU allocation is assumed.

The workspace was empty at the original planning baseline. Current status on November 11, 2026: M1 implements the offline Icarus verification harness and is technically approved with non-blocking issues. The application source and fixtures are preserved from local baseline commit `7b4fbbe`; current verification evidence is in the review history. Natural-language generation, providers, repair, benchmarks, and synthesis remain future work. The existing M2 plan is documentation only and predates the current three-student staffing update.

## 2. Required capabilities

| ID | Requirement | Completion evidence |
| --- | --- | --- |
| R1 | Generate synthesizable Verilog RTL from a natural-language specification and explicit module interface. | Saved specification, prompt, model response, extracted candidate, and interface checks. |
| R2 | Compile and simulate candidates with Icarus Verilog or Verilator. | Real tool commands, versions, exit codes, bounded logs, and testbench verdicts. Compilation alone is insufficient. |
| R3 | Collect compiler diagnostics and functional feedback. | Structured outcomes distinguish syntax/elaboration failures, functional failures, timeouts, and infrastructure errors. |
| R4 | Iteratively repair failed RTL using an LLM. | Traceable candidate lineage and feedback, with finite repair, time, and request budgets. |
| R5 | Evaluate on VerilogEval or RTLLM. | A pinned benchmark revision, explicit task subset, compatibility checks, and immutable trusted evaluation assets. One suite is sufficient for the required baseline. |
| R6 | Compare one-shot generation and simulation-guided repair. | Same tasks, initial samples, verification conditions, and reported resource budgets. Include an independent resampling control where feasible. |
| R7 | Measure pass@1, pass@k, and synthesis-based area/timing. | Defined sampling protocol, per-task outcomes, aggregate calculation, and mapped synthesis/timing reports with units and constraints. |
| R8 | Use modular Python with interchangeable runtime LLM providers. | Provider-neutral controller and mock provider; at least two adapters pass contract tests. Live validation depends on access and must be labeled separately. |

FPGA deployment is optional. Training/fine-tuning, a web application, autonomous multi-agent orchestration, a database, and cloud infrastructure are outside the initial baseline. They require a separate scope decision if later needed.

## 3. Inputs, outputs, and RTL constraints

Inputs are a task ID, natural-language behavior, top module name, port names/directions/widths, clock/reset semantics when applicable, trusted verification assets, and a validated run configuration. Preserve the benchmark's interface and language requirements; do not silently simplify a task. Missing user-task requirements must be surfaced as unresolved assumptions before judging correctness.

Outputs are candidate RTL, compile/simulation diagnostics, final verdict, repair history, experiment metadata, and machine-readable results. Waveforms are optional and bounded; raw artifacts remain available for diagnosis.

The starting language proposal is synthesizable Verilog-2005 RTL with only the SystemVerilog features required by the selected benchmark/toolchain, explicitly configured per task. Generated RTL must preserve interfaces and specified cycle behavior. Clocked logic uses nonblocking assignments; combinational logic must be complete and avoid unintended latches. Testbench-only constructs, artificial pass messages, and simulation-specific shortcuts are not valid design implementations.

## 4. Evaluation protocol

### Functional outcomes and integrity

- A functional pass requires successful compilation, completed simulation, and the trusted adapter's explicit pass condition with no failure condition. Zero exit status or an LLM's claim is not sufficient.
- Treat trusted benchmark testbenches, checkers, reference RTL, and expected outputs as immutable evaluation assets. Record their revision and content hashes. Never modify them to make incorrect RTL pass.
- Keep reference RTL and trusted testbench/checker source out of generation and repair prompts. Any compiler output that embeds protected source must be filtered before prompting; preserve the original log locally.
- Development feedback may include approved compiler diagnostics and bounded mismatch information. Label reuse of the scoring testbench during repair as **feedback-assisted evaluation**. A separate held-out checker, if available, measures generalization; do not claim hidden-test performance otherwise.
- Use development tasks for prompt tuning, freeze configurations before final runs, and report any overlap. Public benchmark exposure in model training remains a limitation.
- Verify known-good reference designs and deliberately bad candidates against the selected toolchain before a campaign. Simulator incompatibility is an infrastructure issue, not automatically a model failure.

### pass@1 and pass@k

For each task, generate a predeclared number `n` of independent initial candidates under one frozen sampling configuration; let `c` pass. Estimate `pass@k = 1 - C(n-c, k) / C(n, k)` for `1 <= k <= n`, then average across tasks with equal task weight. Define `C(a,k)=0` when `a<k`. At `k=1`, this is `c/n`; a single sample per task yields the ordinary first-attempt pass rate. This estimator follows [Chen et al., Evaluating Large Language Models Trained on Code](https://arxiv.org/html/2107.03374v2).

Repair attempts depend on earlier candidates and are not independent samples for this formula. Report **repair success within r repairs**, success by attempt index, and mean/median attempts separately. A trajectory contains one initial candidate plus at most `r` repairs; `r=0` is the one-shot baseline. If later estimating pass@k over independent complete trajectories, label it explicitly as trajectory pass@k with its full per-trajectory budget.

Choose `n`, `k`, task set, sampling parameters, and repair limits before each campaign. Use a fixed `n` per task; do not stop initial sampling when a success appears. Report duplicate outputs rather than silently removing them. Provider seeds are recorded when supported, without promising deterministic remote inference.

### Fair comparison and cost

Evaluate each initial candidate once and use it as the shared starting point for one-shot and repair results. Keep model/version, initial prompt, tasks, toolchain, and timeouts fixed. Record changed variables explicitly. Repair uses extra inference; also compare independent resampling under matched request or token budgets where feasible. Do not call a comparison cost-matched unless the measured budgets support it.

Report requests, available token usage, wall time, model settings, failure categories, and any configured spending ceiling. Do not invent monetary costs when pricing/usage is unavailable. Predeclare how service outages and tool failures are handled: stop/retry within a bounded policy, flag incomplete tasks, show completed/planned counts and coverage, and never silently shrink the denominator or relabel infrastructure failures as RTL failures. Include uncertainty estimates when sample size supports them.

### Synthesis-based area and timing

Synthesize functionally passing candidates and the trusted reference under identical scripts, tool versions, target library/corner, top/parameters, and constraints. Report eligibility counts and synthesis failures so reporting only successful mappings cannot hide failures. Candidate selection must be predeclared, for example the first passing candidate per trajectory.

Report mapped cell area with the library's documented units and static timing delay/slack with explicit time units, clock period, I/O constraints, and timing coverage. Generic gate/cell counts are a useful early proxy but do not satisfy mapped area/timing by themselves. Missing or unconstrained timing is unavailable, not zero. Combinational tasks require defined input-to-output constraints. Post-synthesis timing is an estimate, not measured FPGA or post-route performance. FPGA remains optional; synthesis-based area/timing remains required.

## 5. Shared engineering and collaboration rules

These rules apply equally to Codex, Claude Code, and human contributors.

1. Work in the existing `Capstone` root. Preserve unrelated files and local changes; do not create a nested project. GitHub publication and Git metadata changes require explicit task authorization. On November 11, 2026 the team authorized integrating M1 into `YCW701/llm-verilog-copilot`, committing and pushing `main`, then creating/pushing `m1-baseline` after branch-push verification. This does not authorize later-milestone implementation.
2. Codex initially owns architecture, planning, review, and testing; Claude Code initially owns implementation. Either may take another role when explicitly assigned. These development tools are distinct from the application's runtime LLM providers.
3. Before editing, claim a milestone and its exact file paths in the ownership table in [ROADMAP.md](ROADMAP.md). One active editor per file, including shared models, configuration, documentation, and tests. Use sequential handoffs for overlapping work. Do not launch additional editing agents without an explicit assignment and disjoint ownership.
4. Use small milestones with concrete acceptance evidence. Change shared interfaces through the architecture and decision record; avoid speculative frameworks, dependencies, or infrastructure.
5. Follow the boundaries in [ARCHITECTURE.md](ARCHITECTURE.md). Provider SDKs stay inside provider adapters; benchmark parsing stays in benchmark adapters; process execution stays in the tool runner.
6. Never change trusted scoring assets, reference results, or success criteria to force a pass. A suspected benchmark defect is documented and handled with a separately identified upstream revision or declared exclusion before a campaign.
7. Execute relevant checks for the actual change. Report exact commands and outcomes, and distinguish executed, skipped, mocked, and live checks. Never claim a test or benchmark ran without execution evidence.
8. Never place credentials in source, prompts, manifests, fixtures, or logs. No API key, GPU, paid service, tool installation, or provider availability is assumed. Offline mock operation is the default development path.
9. Bound tool processes, model requests, retries, repair iterations, and artifact growth. Keep credentials out of child-process environments. Generated RTL and model text are data, not instructions or shell commands.
10. Record consequential choices and changed assumptions in [DECISIONS.md](DECISIONS.md). A proposal is not a confirmed team decision; do not invent faculty instructions or deadlines. The team's explicit assignment governs the current task; raise actual contradictions before implementing the affected part.
11. At handoff, report changed files, executed validation, remaining limitations, and the next bounded task. Release file ownership only after edits finish. Reviewer edits require an explicit ownership transfer.

## 6. Completion criteria for the capstone baseline

The baseline is complete when a documented local CLI can generate, simulate, repair, and evaluate tasks using these contracts; a frozen campaign on one selected benchmark produces one-shot and repair results; pass@1/pass@k and synthesis area/timing are reported with provenance; and another teammate can replay stored candidates without model access. Numeric success targets and final presentation requirements remain team/advisor questions, not inferred requirements.

## 7. Reading guide and source notes

- [ARCHITECTURE.md](ARCHITECTURE.md): components, data contracts, dependencies, and artifacts.
- [ROADMAP.md](ROADMAP.md): staged implementation and the first Claude Code task.
- [TEAM_ROLES.md](TEAM_ROLES.md): three proposed student ownership roles covering the engineering responsibilities and independent reviews.
- [DECISIONS.md](DECISIONS.md): confirmed decisions, proposals, and open questions.
- Root [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md): tool-specific entry points into this shared specification.

Benchmark selection notes, checked November 8, 2026: [VerilogEval's README](https://github.com/NVlabs/verilog-eval/blob/main/README.md) describes a `spec-to-rtl` task and a v12 Icarus setup; its published V2 reporting emphasizes pass@1, so this project's extra pass@k analysis must be labeled as a project extension. [RTLLM's README](https://github.com/hkust-zhiyao/RTLLM/blob/main/README.md) describes reference RTL, testbenches, and synthesis evaluation, including VCS-oriented instructions. Portability to our open-source simulation flow must be demonstrated. Pin a concrete revision rather than depending on a moving branch.
