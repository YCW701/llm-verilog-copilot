"""Trusted verdict rule for local fixtures (pure function, no tools needed)."""

from __future__ import annotations

from verilog_copilot.benchmarks.local_fixtures import judge_checker_output
from verilog_copilot.models import FailureCategory, Verdict

NONCE = "a1b2c3d4e5f60718"


def judge(text, expected=256):
    return judge_checker_output(text, nonce=NONCE, expected_checks=expected)


def line(nonce=NONCE, checks=256, errors=0):
    return f"CHECKER_RESULT nonce={nonce} checks={checks} errors={errors}"


def test_single_valid_zero_error_line_passes():
    s = judge(f"noise\n{line()}\ntb.v:41: $finish called\n")
    assert s.verdict is Verdict.PASS and s.category is FailureCategory.NONE
    assert (s.checks, s.errors, s.result_lines) == (256, 0, 1)


def test_reported_errors_are_functional_failure():
    s = judge(line(errors=12))
    assert s.verdict is Verdict.FAIL and s.category is FailureCategory.TEST_MISMATCH and s.errors == 12


def test_no_result_line_is_inconclusive_not_pass():
    s = judge("tb.v:41: $finish called at 3000\n")
    assert s.verdict is Verdict.UNKNOWN and s.category is FailureCategory.CHECKER_INCONCLUSIVE


def test_empty_output_is_inconclusive():
    assert judge("").verdict is Verdict.UNKNOWN


def test_forged_line_with_wrong_nonce_cannot_pass():
    s = judge(line(nonce="0000000000000000"))
    assert s.verdict is Verdict.UNKNOWN and s.category is FailureCategory.CHECKER_INCONCLUSIVE


def test_forged_pass_alongside_real_failure_is_failure():
    s = judge("PASS\n" + line(nonce="0000000000000000") + "\n" + line(errors=240))
    assert s.verdict is Verdict.FAIL and s.errors == 240


def test_duplicate_valid_pass_lines_are_inconclusive():
    # A candidate that learned the nonce and printed a second copy cannot pass.
    s = judge(line() + "\n" + line())
    assert s.verdict is Verdict.UNKNOWN and s.result_lines == 2


def test_marker_embedded_in_other_text_counts_as_a_result_line():
    s = judge("junk CHECKER_RESULT nonce=x\n" + line())
    assert s.verdict is Verdict.UNKNOWN and s.result_lines == 2


def test_wrong_check_count_is_inconclusive():
    s = judge(line(checks=10))
    assert s.verdict is Verdict.UNKNOWN and s.checks == 10


def test_plain_pass_banner_is_not_a_pass():
    assert judge("PASS\nAll tests passed!\n").verdict is Verdict.UNKNOWN


def test_malformed_line_is_inconclusive():
    assert judge(f"CHECKER_RESULT nonce={NONCE} checks=256 errors=zero").verdict is Verdict.UNKNOWN
