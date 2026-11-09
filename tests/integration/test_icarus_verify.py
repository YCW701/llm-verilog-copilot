"""M1 acceptance checks against real Icarus Verilog. Skipped (and labeled) when
iverilog/vvp are not installed."""

from __future__ import annotations

import dataclasses
import errno
import shutil
import time
from pathlib import Path

import pytest

from conftest import requires_icarus
from verilog_copilot.benchmarks import local_fixtures
from verilog_copilot.models import CandidateOrigin, FailureCategory, StageStatus, TrustedFile, Verdict
from verilog_copilot.storage import create_run_dir, sha256_file
from verilog_copilot.tools.icarus import find_tools
from verilog_copilot.tools import process
from verilog_copilot.tools.simulation import SimulationLimits, _verify_impl, verify

pytestmark = [pytest.mark.integration, requires_icarus]

LIMITS = SimulationLimits(compile_timeout_s=30, simulation_timeout_s=10, max_log_bytes=256 * 1024)


def _verify(rtl: Path, run_dir: Path, limits: SimulationLimits = LIMITS, bundle=None):
    """Supported execution path (origin gate + RTL admission screen)."""
    return verify(rtl, bundle or local_fixtures.get_bundle("adder4"), limits, create_run_dir(run_dir), find_tools(),
                  origin=CandidateOrigin.TEAM_AUTHORED)


def _verify_inner(rtl: Path, run_dir: Path, limits: SimulationLimits = LIMITS):
    """Inner defense layer only: RTL screen skipped so the checker/oracle and runner
    protections can be exercised on reviewed team fixtures that the screen rejects."""
    return _verify_impl(rtl, local_fixtures.get_bundle("adder4"), limits, create_run_dir(run_dir), find_tools(),
                        origin=CandidateOrigin.TEAM_AUTHORED, screen_rtl=False)


def test_correct_candidate_passes_with_full_evidence(tmp_path, candidate):
    rtl = candidate("correct")
    before = sha256_file(rtl)
    res = _verify(rtl, tmp_path / "run")
    assert res.verdict is Verdict.PASS and res.failure_category is FailureCategory.NONE
    assert res.compile.status is StageStatus.OK and res.simulation.status is StageStatus.OK
    assert res.checker and res.checker.checks == 256 and res.checker.errors == 0
    # Evidence: commands, versions, hashes, durations, log paths.
    assert "iverilog" in Path(res.compile.process.argv[0]).name
    assert "vvp" in Path(res.simulation.process.argv[0]).name
    assert res.compile.tool_version and "Icarus Verilog" in res.compile.tool_version
    assert res.simulation.tool_version and "Icarus Verilog" in res.simulation.tool_version
    assert res.compile.process.duration_s > 0 and res.simulation.process.duration_s > 0
    for p in (res.compile.process.stdout_path, res.compile.process.stderr_path,
              res.simulation.process.stdout_path, res.simulation.process.stderr_path):
        assert Path(p).is_file()
    assert res.candidate_source.sha256 == res.candidate_copy.sha256 == before
    assert sha256_file(rtl) == before, "input RTL was modified"
    assert res.trusted_files[0].sha256 == local_fixtures.get_bundle("adder4").trusted_files[0].sha256
    assert res.integrity_errors == []


def test_wrong_behavior_compiles_and_fails_functionally(tmp_path, candidate):
    res = _verify(candidate("wrong_behavior"), tmp_path / "run")
    assert res.compile.status is StageStatus.OK and res.simulation.status is StageStatus.OK
    assert res.verdict is Verdict.FAIL and res.failure_category is FailureCategory.TEST_MISMATCH
    assert res.checker.errors > 0


def test_syntax_error_fails_compile_and_never_simulates(tmp_path, candidate):
    run = tmp_path / "run"
    res = _verify(candidate("syntax_error"), run)
    assert res.compile.status is StageStatus.FAILED
    assert res.verdict is Verdict.FAIL and res.failure_category is FailureCategory.COMPILE_ERROR
    assert res.simulation.status is StageStatus.NOT_RUN and res.simulation.process is None
    assert not (run / "simulation.stdout.log").exists()
    assert "syntax error" in (run / "compile.stderr.log").read_text()


def test_nonterminating_simulation_times_out_with_bounded_logs(tmp_path, candidate):
    limits = dataclasses.replace(LIMITS, simulation_timeout_s=2.0, max_log_bytes=64 * 1024)
    t0 = time.monotonic()
    res = _verify_inner(candidate("hang"), tmp_path / "run", limits)  # flooding hang uses $display
    assert time.monotonic() - t0 < 15
    assert res.simulation.status is StageStatus.TIMEOUT
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.SIMULATION_TIMEOUT
    proc = res.simulation.process
    assert proc.timed_out and proc.signal is not None
    assert proc.stdout_truncated and Path(proc.stdout_path).stat().st_size <= 64 * 1024
    assert res.checker is None


def test_exit_zero_without_checker_completion_cannot_pass(tmp_path, candidate):
    res = _verify_inner(candidate("early_finish"), tmp_path / "run")  # inner oracle layer
    assert res.simulation.status is StageStatus.OK and res.simulation.process.exit_code == 0
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.CHECKER_INCONCLUSIVE


def test_fake_pass_text_cannot_override_checker(tmp_path, candidate):
    run = tmp_path / "run"
    res = _verify_inner(candidate("fake_pass"), run)  # inner oracle layer
    assert "PASS" in (run / "simulation.stdout.log").read_text()
    assert res.verdict is Verdict.FAIL and res.failure_category is FailureCategory.TEST_MISMATCH


def test_missing_tool_is_infrastructure_error(tmp_path, candidate):
    tools = find_tools(iverilog=str(tmp_path / "nope"), vvp=shutil.which("vvp"))
    res = verify(candidate("correct"), local_fixtures.get_bundle("adder4"), LIMITS, create_run_dir(tmp_path / "r"), tools,
                 origin=CandidateOrigin.TEAM_AUTHORED)
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.MISSING_TOOL
    assert res.compile.status is StageStatus.TOOL_ERROR and res.simulation.status is StageStatus.NOT_RUN


def test_tampered_checker_blocks_the_run(tmp_path, candidate):
    real = local_fixtures.get_bundle("adder4")
    tampered = tmp_path / "tb_adder4.v"
    tampered.write_text(real.trusted_files[0].path.read_text().replace("errors = errors + 1;", ";"))
    bundle = dataclasses.replace(real, trusted_files=(TrustedFile(tampered, real.trusted_files[0].sha256),))
    res = _verify(candidate("wrong_behavior"), tmp_path / "run", bundle=bundle)
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.INFRASTRUCTURE_ERROR
    assert res.compile.status is StageStatus.NOT_RUN and res.integrity_errors


def test_paths_with_spaces(tmp_path, candidate):
    src_dir = tmp_path / "my rtl dir"
    src_dir.mkdir()
    rtl = src_dir / "my adder.v"
    shutil.copyfile(candidate("correct"), rtl)
    res = _verify(rtl, tmp_path / "output dir" / "run 1")
    assert res.verdict is Verdict.PASS


# --- M1 correction regressions (review findings M1-C1, M1-C3, M1-I1) -----------------


@pytest.mark.parametrize("name", ["nonce_forgery", "hierarchical_tamper", "fake_pass", "early_finish", "hang"])
def test_interfering_candidates_are_rejected_before_compilation(tmp_path, candidate, name):
    run = tmp_path / "run"
    res = _verify(candidate(name), run)
    assert res.verdict is Verdict.FAIL
    assert res.failure_category is FailureCategory.CANDIDATE_POLICY_VIOLATION
    assert res.rtl_screen is StageStatus.FAILED and res.policy_violations
    assert res.compile.status is StageStatus.NOT_RUN and res.simulation.status is StageStatus.NOT_RUN
    assert not (run / "sim.vvp").exists() and not (run / "compile.stdout.log").exists()


def test_review_nonce_forgery_probe_cannot_pass(tmp_path, candidate):
    """M1-C1 verbatim probe: before the fix this returned pass/none."""
    res = _verify(candidate("nonce_forgery"), tmp_path / "run")
    assert res.verdict is not Verdict.PASS
    assert any("$value$plusargs" in v for v in res.policy_violations)


def test_hierarchical_tamper_cannot_pass(tmp_path, candidate):
    """No system tasks; writes tb_adder4.errors through an upward reference."""
    res = _verify(candidate("hierarchical_tamper"), tmp_path / "run")
    assert res.verdict is not Verdict.PASS
    assert any("hierarchical reference" in v for v in res.policy_violations)


@pytest.mark.parametrize("name,verdict,category", [
    ("correct", Verdict.PASS, FailureCategory.NONE),
    ("wrong_behavior", Verdict.FAIL, FailureCategory.TEST_MISMATCH),
    ("syntax_error", Verdict.FAIL, FailureCategory.COMPILE_ERROR),
])
def test_admitted_fixtures_keep_their_classification(tmp_path, candidate, name, verdict, category):
    res = _verify(candidate(name), tmp_path / "run")
    assert res.rtl_screen is StageStatus.OK and res.policy_violations == []
    assert (res.verdict, res.failure_category) == (verdict, category)


def test_silent_hang_times_out_through_supported_path(tmp_path, candidate):
    limits = dataclasses.replace(LIMITS, simulation_timeout_s=2.0)
    res = _verify(candidate("hang_silent"), tmp_path / "run", limits)
    assert res.rtl_screen is StageStatus.OK
    assert res.simulation.status is StageStatus.TIMEOUT and res.simulation.process.timed_out
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.SIMULATION_TIMEOUT


def test_simulation_log_write_failure_cannot_pass(tmp_path, candidate, monkeypatch):
    """M1-I1: without capture-error propagation this correct design would pass."""
    real_write = process._BoundedPump._write_chunk

    def failing_write(self, out, data):
        if self._dest.name == "simulation.stdout.log":
            raise OSError(errno.ENOSPC, "No space left on device (simulated)")
        return real_write(self, out, data)

    monkeypatch.setattr(process._BoundedPump, "_write_chunk", failing_write)
    res = _verify(candidate("correct"), tmp_path / "run")
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.INFRASTRUCTURE_ERROR
    assert res.simulation.status is StageStatus.TOOL_ERROR
    assert any("No space left" in e for e in res.simulation.process.capture_errors)
    assert res.checker is None


# --- M1-R2 corrections (review M1_REVIEW_R2.md: C1 lexer bypasses, I1 version probes) --
# Candidates are built from bytes and written with write_bytes so no line-ending
# normalization can occur; each test asserts the intended bytes are on disk.

R2_LONE_CR_PAYLOAD = (  # verbatim from M1_REVIEW_R2.md section 4
    b"module adder4(input [3:0] a,b,output [4:0] sum);\n"
    b"assign sum=0; // ignored?\r"
    b"reg [511:0] n; initial begin "
    b'if ($value$plusargs("checker_nonce=%s",n)) '
    b'$display("CHECKER_RESULT nonce=%0s checks=256 errors=0",n); '
    b"$finish; end\nendmodule\n"
)
_HEAD = b"module adder4(input [3:0] a, input [3:0] b, output [4:0] sum);\nassign sum = 0;\n"
_FORGERY = (b"reg [511:0] n; initial begin "
            b'if ($value$plusargs("checker_nonce=%s",n)) '
            b'$display("CHECKER_RESULT nonce=%0s checks=256 errors=0",n); $finish; end')
_TERMINATORS = (b"\n", b"\r", b"\r\n")
_SEPARATORS = [bytes([c]) for c in range(1, 32) if c not in (10, 13)] + [
    b"\x7f", "\u0085".encode(), " ".encode(), " ".encode(), *_TERMINATORS]
_TEMPLATES = {
    "comment": lambda s: _HEAD + b"// c" + s + _FORGERY + b"\nendmodule\n",
    "comment_then_block": lambda s: _HEAD + b"// x" + s + b"/*\n" + _FORGERY + b"\n// */\nendmodule\n",
    "string": lambda s: _HEAD + b'localparam [15:0] S = "a' + s + b'"; ' + _FORGERY + b"\nendmodule\n",
    "string_continuation": lambda s: _HEAD + b'localparam [15:0] S = "a\\' + s + b'"; ' + _FORGERY + b"\nendmodule\n",
}


def _write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    assert path.read_bytes() == data
    return path


@pytest.mark.parametrize("ending", [b"\r", b"\r\n", b"\n"], ids=["cr", "crlf", "lf"])
def test_r2_lone_cr_payload_cannot_pass(tmp_path, ending):
    """M1-R2 C1 reproduction. The unscreened inner layer is genuinely fooled
    (pass), so it is the screen that must reject it, in every line-ending form."""
    data = R2_LONE_CR_PAYLOAD.replace(b"\r", ending)
    rtl = _write(tmp_path / "probe.v", data)
    if ending == b"\r":
        assert data == R2_LONE_CR_PAYLOAD and b"\r" in rtl.read_bytes() and b"// ignored?\r" in data
    inner = _verify_inner(rtl, tmp_path / "inner")
    assert inner.verdict is Verdict.PASS, "probe no longer forges a pass; regression is not meaningful"
    res = _verify(rtl, tmp_path / "run")
    assert res.verdict is Verdict.FAIL and res.failure_category is FailureCategory.CANDIDATE_POLICY_VIOLATION
    assert res.rtl_screen is StageStatus.FAILED and res.compile.status is StageStatus.NOT_RUN
    assert not (tmp_path / "run" / "sim.vvp").exists()
    assert (tmp_path / "run" / "candidate.v").read_bytes() == data, "screened/compiled copy must be byte-exact"


@pytest.mark.parametrize("template", list(_TEMPLATES))
def test_differential_separator_sweep_never_passes(tmp_path, template):
    """For every control/Unicode separator: whenever Icarus actually executes the
    forgery (unscreened inner layer passes), the public path rejects it; and the
    public path never passes."""
    live = []
    for i, sep in enumerate(_SEPARATORS):
        rtl = _write(tmp_path / f"c{i}.v", _TEMPLATES[template](sep))
        res = _verify(rtl, tmp_path / f"pub{i}")
        assert res.verdict is not Verdict.PASS, (template, sep)
        inner = _verify_inner(rtl, tmp_path / f"inner{i}")
        if inner.verdict is Verdict.PASS:
            live.append(sep)
            assert res.failure_category is FailureCategory.CANDIDATE_POLICY_VIOLATION, (template, sep)
    # Known Icarus 13.0 behavior, so the sweep provably exercises live forgeries.
    expected_live = {
        "comment": set(_TERMINATORS),
        "comment_then_block": set(_SEPARATORS) - set(_TERMINATORS),
        "string": set(_SEPARATORS) - set(_TERMINATORS),
        "string_continuation": set(_SEPARATORS),
    }[template]
    assert set(live) == expected_live


@pytest.mark.parametrize("body", [
    # Every forbidden token directly follows a number (no whitespace).
    b"reg [511:0] n; reg ok; initial begin ok = #0$value$plusargs(\"checker_nonce=%s\",n); "
    b"if (ok) #0$display(\"CHECKER_RESULT nonce=%0s checks=256 errors=0\",n); #0$finish; end",
    # Wrong except for the final vector; clears the checker's error count after
    # the last mismatch (t=256 ns, before the final check completes).
    b"`timescale 1ns/1ps\n" + _HEAD.replace(b"assign sum = 0;", b"assign sum = (a == 4'd15 && b == 4'd15) ? 5'd30 : 5'd0;")
    + b"initial #256tb_adder4.errors = 0;",
], ids=["system_tasks_after_delay", "hierarchical_after_delay"])
def test_number_prefixed_forgeries_cannot_pass(tmp_path, body):
    src = body if body.startswith(b"`timescale") else _HEAD + body
    rtl = _write(tmp_path / "probe.v", src + b"\nendmodule\n")
    inner = _verify_inner(rtl, tmp_path / "inner")
    assert inner.verdict is Verdict.PASS, "probe no longer forges a pass; regression is not meaningful"
    res = _verify(rtl, tmp_path / "run")
    assert res.verdict is Verdict.FAIL and res.failure_category is FailureCategory.CANDIDATE_POLICY_VIOLATION


@pytest.mark.parametrize("ending", [b"\n", b"\r\n", b"\r"], ids=["lf", "crlf", "cr"])
@pytest.mark.parametrize("name,verdict,category", [
    ("correct", Verdict.PASS, FailureCategory.NONE),
    ("wrong_behavior", Verdict.FAIL, FailureCategory.TEST_MISMATCH),
])
def test_line_ending_forms_of_benign_fixtures_classify_consistently(tmp_path, candidate, ending, name,
                                                                     verdict, category):
    data = candidate(name).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", ending)
    rtl = _write(tmp_path / "form.v", data)
    if ending != b"\n":
        assert ending in rtl.read_bytes()
    res = _verify(rtl, tmp_path / "run")
    assert res.rtl_screen is StageStatus.OK
    assert (res.verdict, res.failure_category) == (verdict, category)


def _fail_version_open(monkeypatch):
    real_open = open

    def failing_open(path, *args, **kwargs):
        if ".version." in Path(path).name:
            raise PermissionError(errno.EACCES, "Permission denied (simulated)", str(path))
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(process, "open", failing_open, raising=False)


def _fail_version_write(monkeypatch):
    real_write = process._BoundedPump._write_chunk

    def failing_write(self, out, data):
        if ".version." in self._dest.name:
            raise OSError(errno.ENOSPC, "No space left on device (simulated)")
        return real_write(self, out, data)

    monkeypatch.setattr(process._BoundedPump, "_write_chunk", failing_write)


@pytest.mark.parametrize("inject,needle", [(_fail_version_open, "Permission denied"),
                                           (_fail_version_write, "No space left")], ids=["open", "write"])
def test_version_probe_capture_failure_cannot_pass(tmp_path, candidate, monkeypatch, inject, needle):
    """M1-R2 I1 reproduction: before the fix this returned pass/none with null versions."""
    inject(monkeypatch)
    run = tmp_path / "run"
    res = _verify(candidate("correct"), run)
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.INFRASTRUCTURE_ERROR
    assert "version probe failed" in res.message
    for stage in (res.compile, res.simulation):
        assert stage.status is StageStatus.NOT_RUN and stage.process is None
        assert stage.tool_version is None
        assert any(needle in e for e in stage.version_probe.capture_errors)
    assert not (run / "compile.stdout.log").exists() and not (run / "sim.vvp").exists()
    assert res.checker is None


def test_version_probe_evidence_is_recorded(tmp_path, candidate):
    res = _verify(candidate("correct"), tmp_path / "run")
    assert res.verdict is Verdict.PASS
    for stage in (res.compile, res.simulation):
        probe = stage.version_probe
        assert probe is not None and probe.exit_code == 0 and probe.capture_errors == []
        assert probe.argv[-1] == "-V" and Path(probe.stdout_path).is_file()
        assert "Icarus Verilog" in stage.tool_version
