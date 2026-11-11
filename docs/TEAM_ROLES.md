# Team Roles

Rutgers ECE Capstone, Group 62 — **three undergraduate ECE students**, academic year **2026–2027**. Faculty advisor: Professor Hang Liu. Updated November 11, 2026 from the team's current project information. Names and assignments are not yet supplied; these are three proposed substantial engineering roles, not named appointments. Each student owns implementation, tests, documentation, and review evidence for a subsystem. The earlier four-role M2 plan is retained as historical planning and must be reassigned before implementation; no M2 work is started by this staffing update.

## 1. Platform, architecture, and evaluation engineer

Own the Python package, CLI/configuration, common data contracts, controller integration, artifact schema/storage, and reproducible setup. Establish dependency boundaries and backward-compatible result formats. Integrate milestones without allowing provider or tool details into orchestration.

Own experiment manifests, independent-sampling definitions, pass@1/pass@k calculations, repair-success accounting, budget comparisons, and result summaries when those milestones are assigned.

Deliverables: M1 package/CLI and artifact foundation; future M2/M3 integration; schema/contract tests; replay/setup instructions; later metric tests, frozen experiment configurations, and evaluation reports. Review Role 3's synthesis/report provenance. Do not become the sole implementer: each subsystem owner integrates against agreed contracts. These future deliverables are responsibilities, not completed features.

## 2. LLM and repair engineer

Own provider-neutral request/response adapters, offline mock behavior, prompt versions, deterministic RTL extraction, and bounded repair policy. Investigate failure modes and tune prompts on development tasks before final protocol freeze. Separate request retries from RTL repairs and track usage/latency.

Deliverables: two adapter contract implementations, one-shot generation path, repair lineage/stop behavior, sanitized feedback integration, and prompt ablations. Live adapter validation is conditional on access. Review Role 1's controller behavior and ensure no reference/testbench source reaches provider prompts.

## 3. RTL verification, benchmark, and synthesis engineer

Own process-runner execution behavior, simulator adapter, trusted test/checker policy, benchmark import/provenance, and compatibility qualification. Cover combinational and sequential behavior, reset/cycle semantics, syntax failures, mismatches, hangs, and ambiguous verdicts. Preserve trusted benchmark assets and independently validate oracle behavior.

Own later synthesis/library/constraint qualification and mapped area/static-timing comparisons against references, with units, eligibility counts, coverage and failure evidence. Coordinate numerical aggregation with Role 1.

Deliverables: real Icarus compile/simulation harness and miniature regression fixtures; later, an optional justified Verilator adapter, a qualified benchmark adapter, integrity/compatibility evidence, and a reproducible synthesis/static-timing flow. Review Role 2's RTL/interface validation and repair feedback for leakage or false pass conditions. Benchmark and synthesis work remain future milestones.

## Shared operation and review

| Engineering responsibility | Primary owner | Independent reviewer |
| --- | --- | --- |
| Contracts, CLI, controller, artifacts | Role 1 | Role 2 |
| Providers, extraction, prompts, repair | Role 2 | Role 3 |
| Process execution, simulation, benchmark integrity | Role 3 | Role 1 |
| Sampling, metrics, experiment/report accounting | Role 1 | Role 2 |
| Synthesis/timing and reference comparisons | Role 3 | Role 1 |

Every role contributes code and validation; testing and documentation are not isolated into a lightweight role. These ownership areas do not authorize concurrent edits to shared files. Shared models/controller changes require the exact-file handoff in [ROADMAP.md](ROADMAP.md). The reviewer may inspect while implementation proceeds, but cannot edit the same files simultaneously.

Codex initially supports architecture, task planning, technical review, and test execution. Claude Code initially supports implementation. These are tool assignments, not substitutes for student responsibility or runtime provider choices. Either tool may perform other work when explicitly assigned. Students own acceptance of outputs, technical understanding, and decisions.

Professor Hang Liu is the faculty advisor. No meeting schedule, review obligation, preferred technology, deadline, or approval is invented here. Team members should bring unresolved scope/evaluation questions from [DECISIONS.md](DECISIONS.md) to appropriate team/advisor discussions and record actual outcomes.
