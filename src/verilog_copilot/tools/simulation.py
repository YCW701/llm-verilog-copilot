"""Simulation contract: compile and execute a candidate against a trusted bundle.

``verify(candidate, bundle, limits, run_dir, tools, *, origin) -> VerificationResult``

Supported execution path (``verify``):

1. Execution gate: only ``CandidateOrigin.TEAM_AUTHORED`` RTL is executed.
   ``MODEL_GENERATED`` RTL is refused until an execution-safety policy is adopted
   (DECISIONS Q05). The origin is a required, caller-declared argument -- an API
   tripwire, not proof of authorship.
2. Trusted files must match their pinned hashes (before and after the run).
3. The private candidate copy must pass the RTL admission screen
   (``verilog_copilot.rtl``) before it is compiled.
4. Both tool version probes are recorded (spawn, capture, timeout and signal
   failures stop the run before compilation as unknown/infrastructure_error).
5. Compilation succeeds, simulation exits 0 within its deadline, all log
   capture succeeds, and the bundle's trusted verdict rule reports pass.

Exit status alone never produces a pass.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from verilog_copilot.models import (
    CandidateOrigin,
    CheckerSummary,
    FailureCategory,
    FileRecord,
    ProcessResult,
    StageResult,
    StageStatus,
    Verdict,
    VerificationBundle,
    VerificationResult,
)
from verilog_copilot.rtl import screen_candidate_rtl
from verilog_copilot.storage import copy_file_exclusive, sha256_file
from verilog_copilot.tools import icarus
from verilog_copilot.tools.icarus import IcarusTools
from verilog_copilot.tools.process import run_process

CANDIDATE_NAME = "candidate.v"
COMPILED_NAME = "sim.vvp"


@dataclass(frozen=True)
class SimulationLimits:
    compile_timeout_s: float = 30.0
    simulation_timeout_s: float = 10.0
    max_log_bytes: int = 1024 * 1024
    max_candidate_bytes: int = 1024 * 1024


def _hash_or_none(path: Path) -> str | None:
    try:
        return sha256_file(path)
    except OSError:
        return None


def _check_trusted(bundle: VerificationBundle) -> tuple[list[FileRecord], list[str]]:
    records, errors = [], []
    for tf in bundle.trusted_files:
        actual = _hash_or_none(tf.path)
        records.append(FileRecord(path=str(tf.path), sha256=actual))
        if actual is None:
            errors.append(f"trusted file not readable: {tf.path}")
        elif actual != tf.sha256:
            errors.append(f"trusted file hash mismatch: {tf.path} (expected {tf.sha256}, got {actual})")
    return records, errors


def _classify_process(
    stage: StageResult,
    proc: ProcessResult,
    tool: str,
    timeout_s: float,
    timeout_category: FailureCategory,
    nonzero_exit: tuple[Verdict, FailureCategory],
) -> tuple[Verdict, FailureCategory, str] | None:
    """Set ``stage`` status from a process record. Returns a terminal
    (verdict, category, message), or None when the stage succeeded.

    Order matters: spawn error, then capture error (evidence incomplete), then
    timeout, then signal termination (infrastructure, never a design verdict),
    then an ordinary non-zero exit.
    """
    stage.process = proc
    if proc.spawn_error:
        stage.status, stage.message = StageStatus.TOOL_ERROR, f"could not start {tool}: {proc.spawn_error}"
        return Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR, stage.message
    if proc.capture_errors:
        stage.status = StageStatus.TOOL_ERROR
        stage.message = f"{tool} output could not be fully recorded: " + "; ".join(proc.capture_errors)
        return Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR, stage.message
    if proc.timed_out:
        stage.status, stage.message = StageStatus.TIMEOUT, f"{tool} exceeded {timeout_s}s; its process group was killed"
        return Verdict.UNKNOWN, timeout_category, stage.message
    if proc.signal is not None:
        stage.status, stage.message = StageStatus.TOOL_ERROR, f"{tool} was terminated by signal {proc.signal}"
        return Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR, stage.message
    if proc.exit_code != 0:
        stage.status, stage.message = StageStatus.FAILED, f"{tool} exited with {proc.exit_code}"
        return (*nonzero_exit, stage.message)
    stage.status = StageStatus.OK
    return None


def verify(
    candidate: Path,
    bundle: VerificationBundle,
    limits: SimulationLimits,
    run_dir: Path,
    tools: IcarusTools,
    *,
    origin: CandidateOrigin,
) -> VerificationResult:
    """Supported execution path. Verify ``candidate`` inside the fresh ``run_dir``."""
    return _verify_impl(candidate, bundle, limits, run_dir, tools, origin=origin, screen_rtl=True)


def _verify_impl(
    candidate: Path,
    bundle: VerificationBundle,
    limits: SimulationLimits,
    run_dir: Path,
    tools: IcarusTools,
    *,
    origin: CandidateOrigin,
    screen_rtl: bool,
) -> VerificationResult:
    """Implementation of ``verify``. ``screen_rtl=False`` exists only so tests can
    exercise the inner checker/oracle defenses on reviewed team fixtures; it is
    not reachable from the CLI and must not be used by other callers."""
    t0 = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()
    candidate = Path(candidate).resolve()
    run_dir = Path(run_dir).resolve()
    copy_path = run_dir / CANDIDATE_NAME

    compile_stage = StageResult()
    sim_stage = StageResult()
    checker: CheckerSummary | None = None
    integrity: list[str] = []
    screen_status = StageStatus.NOT_RUN
    violations: list[str] = []
    src_hash = _hash_or_none(candidate)
    copy_hash: str | None = None

    def finish(verdict: Verdict, category: FailureCategory, message: str) -> VerificationResult:
        # Re-verify trusted assets and the input after all tool runs.
        trusted_after, after_errors = _check_trusted(bundle)
        src_after = _hash_or_none(candidate)
        copy_after = _hash_or_none(copy_path) if copy_path.exists() else None
        if src_hash is not None and src_after != src_hash:
            after_errors.append("input RTL changed during verification")
        if copy_hash is not None and copy_after != copy_hash:
            after_errors.append("candidate copy changed during verification")
        integrity.extend(e for e in after_errors if e not in integrity)
        if after_errors and category is not FailureCategory.INFRASTRUCTURE_ERROR:
            verdict, category = Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR
            message = "integrity check failed after run: " + "; ".join(after_errors)
        return VerificationResult(
            task_id=bundle.task_id,
            candidate_source=FileRecord(str(candidate), src_hash),
            candidate_copy=FileRecord(str(copy_path), copy_hash),
            trusted_files=trusted_after,
            compile=compile_stage,
            simulation=sim_stage,
            verdict=verdict,
            failure_category=category,
            message=message,
            started_at=started_at,
            duration_s=round(time.monotonic() - t0, 6),
            checker=checker,
            candidate_origin=origin,
            rtl_screen=screen_status,
            policy_violations=violations,
            integrity_errors=integrity,
        )

    # 1. Execution gate: model-generated RTL is not executed in M1.
    if origin is not CandidateOrigin.TEAM_AUTHORED:
        return finish(
            Verdict.UNKNOWN, FailureCategory.EXECUTION_POLICY_BLOCKED,
            f"execution of {getattr(origin, 'value', origin)} RTL is blocked until an execution-safety "
            "policy is adopted and validated (DECISIONS Q05); nothing was compiled or simulated",
        )

    # 2. Input candidate.
    if src_hash is None or not candidate.is_file():
        return finish(Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR, f"candidate RTL not readable: {candidate}")
    size = candidate.stat().st_size
    if size > limits.max_candidate_bytes:
        return finish(
            Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR,
            f"candidate RTL is {size} bytes, above the {limits.max_candidate_bytes}-byte limit",
        )

    # 3. Trusted assets must match their pinned hashes before anything runs.
    _, before_errors = _check_trusted(bundle)
    if before_errors:
        integrity.extend(before_errors)
        return finish(Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR, "; ".join(before_errors))

    # 4. Work on a private copy; the caller's file is only read.
    copy_file_exclusive(candidate, copy_path)
    copy_hash = sha256_file(copy_path)
    if copy_hash != src_hash:
        integrity.append("candidate copy hash differs from source")
        return finish(Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR, "candidate copy hash differs from source")

    # 5. Admission screen on the exact bytes that will be compiled.
    if screen_rtl:
        violations.extend(screen_candidate_rtl(copy_path.read_bytes()))
        screen_status = StageStatus.FAILED if violations else StageStatus.OK
        if violations:
            return finish(
                Verdict.FAIL, FailureCategory.CANDIDATE_POLICY_VIOLATION,
                f"candidate rejected by RTL admission screen ({len(violations)} violation(s)); not compiled",
            )

    # 6. Tools.
    if tools.missing:
        msg = "required tool(s) not found: " + ", ".join(tools.missing)
        compile_stage.status = StageStatus.TOOL_ERROR
        compile_stage.message = msg
        return finish(Verdict.UNKNOWN, FailureCategory.MISSING_TOOL, msg)
    assert tools.iverilog and tools.vvp
    env = tools.child_env()
    versions_dir = run_dir / "tool_versions"
    versions_dir.mkdir()
    # Version provenance is required evidence: a probe that cannot be recorded
    # stops the run before compilation (review M1-R2 I1).
    probe_errors = []
    for stage, tool, exe in ((compile_stage, "iverilog", tools.iverilog), (sim_stage, "vvp", tools.vvp)):
        probe = icarus.probe_version(exe, versions_dir, env)
        stage.version_probe, stage.tool_version = probe.process, probe.version
        if probe.error:
            stage.message = f"not run: {tool} version probe failed: {probe.error}"
            probe_errors.append(f"{tool} version probe failed: {probe.error}")
    if probe_errors:
        return finish(
            Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR,
            "tool version evidence could not be recorded; compilation and simulation not run: "
            + "; ".join(probe_errors),
        )

    # 7. Compile.
    argv = icarus.compile_argv(
        tools.iverilog,
        language_flag=bundle.language_flag,
        top=bundle.testbench_top,
        output=COMPILED_NAME,
        sources=[CANDIDATE_NAME, *(str(tf.path) for tf in bundle.trusted_files)],
    )
    proc = run_process(
        argv, cwd=run_dir, timeout_s=limits.compile_timeout_s,
        stdout_path=run_dir / "compile.stdout.log", stderr_path=run_dir / "compile.stderr.log",
        max_log_bytes=limits.max_log_bytes, env=env,
    )
    terminal = _classify_process(
        compile_stage, proc, "iverilog", limits.compile_timeout_s,
        FailureCategory.COMPILE_TIMEOUT, (Verdict.FAIL, FailureCategory.COMPILE_ERROR),
    )
    if terminal:
        return finish(*terminal)
    if not (run_dir / COMPILED_NAME).is_file():
        compile_stage.status = StageStatus.TOOL_ERROR
        compile_stage.message = "iverilog exited 0 but produced no output"
        return finish(Verdict.UNKNOWN, FailureCategory.INFRASTRUCTURE_ERROR, compile_stage.message)
    compile_stage.message = "compiled"

    # 8. Simulate with a fresh per-run nonce the checker must echo back.
    nonce = secrets.token_hex(8)
    argv = icarus.simulate_argv(tools.vvp, compiled=COMPILED_NAME, plusargs=[f"+{bundle.nonce_plusarg}={nonce}"])
    proc = run_process(
        argv, cwd=run_dir, timeout_s=limits.simulation_timeout_s,
        stdout_path=run_dir / "simulation.stdout.log", stderr_path=run_dir / "simulation.stderr.log",
        max_log_bytes=limits.max_log_bytes, env=env,
    )
    terminal = _classify_process(
        sim_stage, proc, "vvp", limits.simulation_timeout_s,
        FailureCategory.SIMULATION_TIMEOUT, (Verdict.UNKNOWN, FailureCategory.SIMULATION_ERROR),
    )
    if terminal:
        return finish(*terminal)
    sim_stage.message = "simulation completed"

    # 9. Trusted verdict rule.
    stdout_text = Path(proc.stdout_path).read_text(encoding="utf-8", errors="replace")
    checker = bundle.judge(stdout_text, nonce=nonce, expected_checks=bundle.expected_checks)
    if proc.stdout_truncated and checker.verdict is Verdict.PASS:
        checker = CheckerSummary(
            Verdict.UNKNOWN, FailureCategory.CHECKER_INCONCLUSIVE, checker.result_lines,
            checker.checks, checker.errors, checker.expected_checks,
            "simulation stdout was truncated; refusing to pass on partial output",
        )
    return finish(checker.verdict, checker.category, checker.detail)
