"""Provider-neutral result records for the M1 verification harness.

These dataclasses are the first concrete implementation of the semantic
contracts in docs/ARCHITECTURE.md section 3 (ProcessResult, VerificationBundle,
VerificationResult). Incompatible changes must bump SCHEMA_VERSION.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

SCHEMA_VERSION = "3"
# Version history:
#   1  initial M1 harness.
#   2  M1 correction: ProcessResult.capture_errors; VerificationResult.candidate_origin,
#      rtl_screen, policy_violations; categories candidate_policy_violation and
#      execution_policy_blocked; signal-terminated tools classified as infrastructure_error.
#   3  M1 R2 correction: StageResult.version_probe (the ``-V`` probe's ProcessResult);
#      a version probe that cannot be recorded makes the result unknown/infrastructure_error.


class StageStatus(str, Enum):
    """Outcome of one tool stage (compile or simulate), independent of verdict."""

    NOT_RUN = "not_run"
    OK = "ok"
    FAILED = "failed"
    TIMEOUT = "timeout"
    TOOL_ERROR = "tool_error"


class Verdict(str, Enum):
    """Functional verdict. ``fail`` means definite evidence of a design defect;
    ``unknown`` means correctness could not be established (timeouts,
    inconclusive checker output, infrastructure problems)."""

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class CandidateOrigin(str, Enum):
    """Who wrote the candidate RTL. Execution of ``model_generated`` RTL is blocked
    until an execution-safety policy is adopted (DECISIONS Q05)."""

    TEAM_AUTHORED = "team_authored"
    MODEL_GENERATED = "model_generated"


class FailureCategory(str, Enum):
    NONE = "none"
    CANDIDATE_POLICY_VIOLATION = "candidate_policy_violation"
    EXECUTION_POLICY_BLOCKED = "execution_policy_blocked"
    COMPILE_ERROR = "compile_error"
    COMPILE_TIMEOUT = "compile_timeout"
    TEST_MISMATCH = "test_mismatch"
    SIMULATION_TIMEOUT = "simulation_timeout"
    SIMULATION_ERROR = "simulation_error"
    CHECKER_INCONCLUSIVE = "checker_inconclusive"
    MISSING_TOOL = "missing_tool"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


@dataclass
class ProcessResult:
    """Evidence from one bounded subprocess execution."""

    argv: list[str]
    cwd: str
    exit_code: int | None
    signal: int | None
    duration_s: float
    timed_out: bool
    stdout_path: str
    stderr_path: str
    stdout_bytes: int
    stderr_bytes: int
    stdout_truncated: bool
    stderr_truncated: bool
    spawn_error: str | None = None
    # Non-empty when stdout/stderr evidence could not be fully recorded.
    capture_errors: list[str] = field(default_factory=list)


@dataclass
class StageResult:
    status: StageStatus = StageStatus.NOT_RUN
    # First version line from the tool's -V probe; None if not recognized.
    tool_version: str | None = None
    process: ProcessResult | None = None
    # Evidence from the tool's -V probe (run before compilation).
    version_probe: ProcessResult | None = None
    message: str = ""


@dataclass
class FileRecord:
    path: str
    sha256: str | None


@dataclass
class CheckerSummary:
    """What the trusted checker reported, as interpreted by the verdict rule."""

    verdict: Verdict
    category: FailureCategory
    result_lines: int
    checks: int | None
    errors: int | None
    expected_checks: int
    detail: str


@dataclass(frozen=True)
class TrustedFile:
    path: Path
    sha256: str


@dataclass(frozen=True)
class VerificationBundle:
    """Trusted verification assets for one task. Never shown to a provider."""

    task_id: str
    description: str
    dut_top: str
    testbench_top: str
    trusted_files: tuple[TrustedFile, ...]
    expected_checks: int
    language_flag: str
    nonce_plusarg: str
    # judge(stdout_text, nonce=..., expected_checks=...) -> CheckerSummary
    judge: Callable[..., CheckerSummary]


@dataclass
class VerificationResult:
    task_id: str
    candidate_source: FileRecord
    candidate_copy: FileRecord
    trusted_files: list[FileRecord]
    compile: StageResult
    simulation: StageResult
    verdict: Verdict
    failure_category: FailureCategory
    message: str
    started_at: str
    duration_s: float
    checker: CheckerSummary | None = None
    candidate_origin: CandidateOrigin | None = None
    # Admission screen of the candidate copy: not_run, ok, or failed.
    rtl_screen: StageStatus = StageStatus.NOT_RUN
    policy_violations: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    integrity_errors: list[str] = field(default_factory=list)


def to_jsonable(obj: Any) -> Any:
    """Convert dataclasses/enums/paths into plain JSON-compatible values."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj) if not callable(getattr(obj, f.name))}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj
