# Team Roles

Rutgers ECE Capstone, Group 62 — four undergraduate ECE students. Faculty advisor: Professor Hang Liu. Names and assignments are not yet supplied; these are four proposed substantial engineering roles, not named appointments. Each student owns implementation, tests, documentation, and review evidence for a subsystem.

## 1. Platform and architecture engineer

Own the Python package, CLI/configuration, common data contracts, controller integration, artifact schema/storage, and reproducible setup. Establish dependency boundaries and backward-compatible result formats. Integrate milestones without allowing provider or tool details into orchestration.

Deliverables: M1 package/CLI and artifact foundation; M2/M3 integration; schema/contract tests; replay and clean-environment setup instructions. Review Role 4's result provenance and reporting interfaces. Do not become the sole implementer: each subsystem owner integrates against agreed contracts.

## 2. LLM and repair engineer

Own provider-neutral request/response adapters, offline mock behavior, prompt versions, deterministic RTL extraction, and bounded repair policy. Investigate failure modes and tune prompts on development tasks before final protocol freeze. Separate request retries from RTL repairs and track usage/latency.

Deliverables: two adapter contract implementations, one-shot generation path, repair lineage/stop behavior, sanitized feedback integration, and prompt ablations. Live adapter validation is conditional on access. Review Role 1's controller behavior and ensure no reference/testbench source reaches provider prompts.

## 3. RTL verification and benchmark engineer

Own process-runner execution behavior, simulator adapter, trusted test/checker policy, benchmark import/provenance, and compatibility qualification. Cover combinational and sequential behavior, reset/cycle semantics, syntax failures, mismatches, hangs, and ambiguous verdicts. Preserve trusted benchmark assets and independently validate oracle behavior.

Deliverables: real Icarus compile/simulation harness, miniature regression fixtures, optional justified Verilator adapter, one qualified benchmark adapter, and integrity/compatibility evidence. Review Role 2's RTL/interface validation and repair feedback for leakage or false pass conditions.

## 4. Evaluation and synthesis engineer

Own experiment manifests, independent-sampling protocol, pass@1/pass@k calculations, repair success reporting, fair budget comparisons, and machine-readable summaries. Establish synthesis/library/constraints early, then produce mapped area and timing comparisons against references with units, eligibility counts, and uncertainty/coverage where applicable.

Deliverables: metric tests with known outcomes, frozen experiment configurations, synthesis/static-timing flow, result tables/plots, failure analysis, and reproducibility package. Review Role 3's benchmark qualification and ensure infrastructure failures and exclusions remain visible.

## Shared operation and review

| Engineering responsibility | Primary owner | Independent reviewer |
| --- | --- | --- |
| Contracts, CLI, controller, artifacts | Role 1 | Role 2 |
| Providers, extraction, prompts, repair | Role 2 | Role 3 |
| Process execution, simulation, benchmark integrity | Role 3 | Role 4 |
| Sampling, metrics, synthesis/timing, reports | Role 4 | Role 1 |

Every role contributes code and validation; testing and documentation are not isolated into a lightweight role. These ownership areas do not authorize concurrent edits to shared files. Shared models/controller changes require the exact-file handoff in [ROADMAP.md](ROADMAP.md). The reviewer may inspect while implementation proceeds, but cannot edit the same files simultaneously.

Codex initially supports architecture, task planning, technical review, and test execution. Claude Code initially supports implementation. These are tool assignments, not substitutes for student responsibility or runtime provider choices. Either tool may perform other work when explicitly assigned. Students own acceptance of outputs, technical understanding, and decisions.

Professor Hang Liu is the faculty advisor. No meeting schedule, review obligation, preferred technology, deadline, or approval is invented here. Team members should bring unresolved scope/evaluation questions from [DECISIONS.md](DECISIONS.md) to appropriate team/advisor discussions and record actual outcomes.
