"""Registry of team-authored M1 fixtures and their trusted verdict rule.

These are synthetic development assets, not benchmark material. Each bundle pins
the sha256 of its trusted checker; a mismatch blocks the run. The checker
sources live in ``tests/fixtures`` (ARCHITECTURE section 7), so the registry
requires a source checkout or editable install of this repository.
"""

from __future__ import annotations

import re
from pathlib import Path

from verilog_copilot.models import (
    CheckerSummary,
    FailureCategory,
    TrustedFile,
    Verdict,
    VerificationBundle,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures"

RESULT_MARKER = "CHECKER_RESULT"
_RESULT_RE = re.compile(r"CHECKER_RESULT nonce=(\S+) checks=(\d+) errors=(\d+)")


def judge_checker_output(stdout_text: str, *, nonce: str, expected_checks: int) -> CheckerSummary:
    """Trusted verdict rule for the local fixtures.

    Pass only if *exactly one* line mentions the result marker, it is
    well-formed, echoes this run's nonce, reports the expected number of checks,
    and reports zero errors. A well-formed nonce-matching line with errors > 0 is
    a functional failure even if forged lines are also present. Anything else
    (no line, duplicates, wrong nonce, wrong check count) is inconclusive.
    """
    marker_lines = [ln.strip() for ln in stdout_text.splitlines() if RESULT_MARKER in ln]
    parsed = []
    for ln in marker_lines:
        m = _RESULT_RE.fullmatch(ln)
        if m and m.group(1) == nonce:
            parsed.append((int(m.group(2)), int(m.group(3))))

    def summary(verdict: Verdict, category: FailureCategory, detail: str,
                checks: int | None = None, errors: int | None = None) -> CheckerSummary:
        return CheckerSummary(verdict, category, len(marker_lines), checks, errors, expected_checks, detail)

    failing = [(c, e) for c, e in parsed if e > 0]
    if failing:
        c, e = failing[0]
        return summary(Verdict.FAIL, FailureCategory.TEST_MISMATCH,
                       f"checker reported {e} mismatching vector(s) out of {c}", c, e)
    if not marker_lines:
        return summary(Verdict.UNKNOWN, FailureCategory.CHECKER_INCONCLUSIVE,
                       "simulation ended without a checker result line")
    if len(marker_lines) > 1:
        return summary(Verdict.UNKNOWN, FailureCategory.CHECKER_INCONCLUSIVE,
                       f"expected exactly one checker result line, found {len(marker_lines)}")
    if not parsed:
        return summary(Verdict.UNKNOWN, FailureCategory.CHECKER_INCONCLUSIVE,
                       "checker result line is malformed or does not carry this run's nonce")
    checks, errors = parsed[0]
    if checks != expected_checks:
        return summary(Verdict.UNKNOWN, FailureCategory.CHECKER_INCONCLUSIVE,
                       f"checker ran {checks} checks, expected {expected_checks}", checks, errors)
    return summary(Verdict.PASS, FailureCategory.NONE,
                   f"checker confirmed {checks}/{expected_checks} vectors with 0 errors", checks, errors)


_REGISTRY: dict[str, VerificationBundle] = {
    "adder4": VerificationBundle(
        task_id="adder4",
        description="4-bit unsigned adder with carry-out: sum[4:0] = a[3:0] + b[3:0] (exhaustive check)",
        dut_top="adder4",
        testbench_top="tb_adder4",
        trusted_files=(
            TrustedFile(
                path=FIXTURE_ROOT / "adder4" / "tb_adder4.v",
                sha256="0436fdfb2619d1308bd923ef7808fcb73e09751aabcba65ea2c80157e3048774",
            ),
        ),
        expected_checks=256,
        language_flag="-g2005",
        nonce_plusarg="checker_nonce",
        judge=judge_checker_output,
    ),
}


def task_ids() -> list[str]:
    return sorted(_REGISTRY)


def get_bundle(task_id: str) -> VerificationBundle:
    try:
        return _REGISTRY[task_id]
    except KeyError:
        raise KeyError(f"unknown fixture task {task_id!r}; known: {', '.join(task_ids())}") from None
