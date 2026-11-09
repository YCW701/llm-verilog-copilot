"""Execution-boundary policy and process classification without Icarus.

Uses /bin/sh stubs in place of iverilog/vvp (shell builtins only, because the
child environment has a minimal PATH)."""

from __future__ import annotations

import os
import stat

import pytest

from verilog_copilot.benchmarks import local_fixtures
from verilog_copilot.models import CandidateOrigin, FailureCategory, StageStatus, Verdict
from verilog_copilot.storage import create_run_dir
from verilog_copilot.tools.icarus import find_tools
from verilog_copilot.tools.simulation import SimulationLimits, verify

pytestmark = pytest.mark.skipif(os.name != "posix", reason="SKIPPED: POSIX shell stubs required")

LIMITS = SimulationLimits(compile_timeout_s=10, simulation_timeout_s=10, max_log_bytes=64 * 1024)
BUNDLE = local_fixtures.get_bundle("adder4")

VERSION_THEN = '#!/bin/sh\nif [ "$1" = "-V" ]; then echo "Stub Icarus Verilog version 0"; exit 0; fi\n'
SELF_SIGTERM = VERSION_THEN + "kill -TERM $$\nsleep 5\n"
COMPILE_OK = VERSION_THEN + 'while [ $# -gt 0 ]; do if [ "$1" = "-o" ]; then : > "$2"; fi; shift; done\nexit 0\n'


def _stub(path, body):
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return str(path)


def _verify(tmp_path, rtl, tools, origin=CandidateOrigin.TEAM_AUTHORED):
    return verify(rtl, BUNDLE, LIMITS, create_run_dir(tmp_path / "run"), tools, origin=origin)


def _no_tools(tmp_path):
    return find_tools(iverilog=str(tmp_path / "absent-iverilog"), vvp=str(tmp_path / "absent-vvp"))


def test_origin_is_a_required_keyword(tmp_path, candidate):
    with pytest.raises(TypeError):
        verify(candidate("correct"), BUNDLE, LIMITS, create_run_dir(tmp_path / "r"), _no_tools(tmp_path))


def test_model_generated_rtl_is_blocked_before_any_execution(tmp_path, candidate):
    run = tmp_path / "run"
    marker = tmp_path / "tool-was-run"
    tool = _stub(tmp_path / "tool", f"#!/bin/sh\n: > '{marker}'\n")
    res = verify(candidate("correct"), BUNDLE, LIMITS, create_run_dir(run), find_tools(tool, tool),
                 origin=CandidateOrigin.MODEL_GENERATED)
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.EXECUTION_POLICY_BLOCKED
    assert res.compile.status is StageStatus.NOT_RUN and res.simulation.status is StageStatus.NOT_RUN
    assert res.candidate_origin is CandidateOrigin.MODEL_GENERATED
    assert not marker.exists(), "a tool was executed for model-generated RTL"
    assert list(run.iterdir()) == [], "nothing should be copied or written for blocked RTL"


@pytest.mark.parametrize("name", ["nonce_forgery", "hierarchical_tamper"])
def test_screen_rejects_before_tool_lookup(tmp_path, candidate, name):
    # Even with no tools installed the policy result is deterministic.
    res = _verify(tmp_path, candidate(name), _no_tools(tmp_path))
    assert res.verdict is Verdict.FAIL and res.failure_category is FailureCategory.CANDIDATE_POLICY_VIOLATION
    assert res.rtl_screen is StageStatus.FAILED


def test_admitted_candidate_then_missing_tool(tmp_path, candidate):
    res = _verify(tmp_path, candidate("correct"), _no_tools(tmp_path))
    assert res.rtl_screen is StageStatus.OK
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.MISSING_TOOL


def test_compiler_terminated_by_signal_is_infrastructure_not_compile_error(tmp_path, candidate):
    """M1-C2: before the fix this returned fail/compile_error."""
    iverilog = _stub(tmp_path / "iverilog", SELF_SIGTERM)
    vvp = _stub(tmp_path / "vvp", VERSION_THEN + "exit 0\n")
    res = _verify(tmp_path, candidate("correct"), find_tools(iverilog, vvp))
    assert res.compile.process.signal == 15 and res.compile.process.exit_code is None
    assert res.compile.status is StageStatus.TOOL_ERROR
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.INFRASTRUCTURE_ERROR
    assert res.simulation.status is StageStatus.NOT_RUN
    assert (tmp_path / "run" / "compile.stderr.log").exists()


def test_simulator_terminated_by_signal_is_infrastructure(tmp_path, candidate):
    iverilog = _stub(tmp_path / "iverilog", COMPILE_OK)
    vvp = _stub(tmp_path / "vvp", SELF_SIGTERM)
    res = _verify(tmp_path, candidate("correct"), find_tools(iverilog, vvp))
    assert res.compile.status is StageStatus.OK
    assert res.simulation.process.signal == 15 and res.simulation.status is StageStatus.TOOL_ERROR
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.INFRASTRUCTURE_ERROR


def test_ordinary_compiler_failure_remains_compile_error(tmp_path, candidate):
    iverilog = _stub(tmp_path / "iverilog", VERSION_THEN + "echo 'candidate.v:1: syntax error' >&2\nexit 2\n")
    vvp = _stub(tmp_path / "vvp", VERSION_THEN + "exit 0\n")
    res = _verify(tmp_path, candidate("correct"), find_tools(iverilog, vvp))
    assert res.compile.status is StageStatus.FAILED and res.compile.process.exit_code == 2
    assert res.verdict is Verdict.FAIL and res.failure_category is FailureCategory.COMPILE_ERROR


# --- M1-R2 I1: version-probe evidence -------------------------------------------------

SIGTERM_ON_VERSION = '#!/bin/sh\nif [ "$1" = "-V" ]; then kill -TERM $$; sleep 5; fi\n' + \
    'while [ $# -gt 0 ]; do if [ "$1" = "-o" ]; then : > "$2"; fi; shift; done\nexit 0\n'
NO_VERSION_LINE = '#!/bin/sh\nif [ "$1" = "-V" ]; then echo "banner without the keyword"; exit 0; fi\n' + \
    'while [ $# -gt 0 ]; do if [ "$1" = "-o" ]; then : > "$2"; fi; shift; done\nexit 0\n'
VERSION_NONZERO = '#!/bin/sh\nif [ "$1" = "-V" ]; then echo "Stub Icarus Verilog version 0"; exit 1; fi\n' + \
    'while [ $# -gt 0 ]; do if [ "$1" = "-o" ]; then : > "$2"; fi; shift; done\nexit 0\n'


def _assert_preflight_blocked(res, run):
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.INFRASTRUCTURE_ERROR
    assert "version probe failed" in res.message
    assert res.compile.status is StageStatus.NOT_RUN and res.compile.process is None
    assert res.simulation.status is StageStatus.NOT_RUN and res.simulation.process is None
    assert not (run / "compile.stdout.log").exists() and not (run / "sim.vvp").exists()


def test_version_probe_terminated_by_signal_blocks_before_compile(tmp_path, candidate):
    iverilog = _stub(tmp_path / "iverilog", SIGTERM_ON_VERSION)
    vvp = _stub(tmp_path / "vvp", COMPILE_OK)
    res = _verify(tmp_path, candidate("correct"), find_tools(iverilog, vvp))
    _assert_preflight_blocked(res, tmp_path / "run")
    assert res.compile.version_probe.signal == 15 and res.compile.tool_version is None
    assert res.simulation.version_probe.exit_code == 0 and res.simulation.tool_version  # vvp probe recorded


@pytest.mark.parametrize("failure", ["open", "write"])
def test_version_probe_capture_failure_blocks_before_compile(tmp_path, candidate, monkeypatch, failure):
    import builtins
    import errno

    from verilog_copilot.tools import process

    if failure == "open":
        def failing_open(path, *args, **kwargs):
            if ".version." in os.path.basename(path):
                raise PermissionError(errno.EACCES, "Permission denied (simulated)", str(path))
            return builtins.open(path, *args, **kwargs)
        monkeypatch.setattr(process, "open", failing_open, raising=False)
    else:
        real_write = process._BoundedPump._write_chunk

        def failing_write(self, out, data):
            if ".version." in self._dest.name:
                raise OSError(errno.ENOSPC, "No space left on device (simulated)")
            return real_write(self, out, data)
        monkeypatch.setattr(process._BoundedPump, "_write_chunk", failing_write)

    tool = _stub(tmp_path / "tool", COMPILE_OK)
    res = _verify(tmp_path, candidate("correct"), find_tools(tool, tool))
    _assert_preflight_blocked(res, tmp_path / "run")
    for stage in (res.compile, res.simulation):
        assert stage.tool_version is None and stage.version_probe.capture_errors
        assert "version probe failed" in stage.message


def test_unrecognized_version_string_is_recorded_not_blocking(tmp_path, candidate):
    """A cleanly recorded probe without a version line is distinguishable from a
    capture failure: tool_version is None but capture_errors is empty."""
    tool = _stub(tmp_path / "tool", NO_VERSION_LINE)
    res = _verify(tmp_path, candidate("correct"), find_tools(tool, tool))
    for stage in (res.compile, res.simulation):
        assert stage.tool_version is None
        assert stage.version_probe.capture_errors == [] and stage.version_probe.exit_code == 0
    assert res.compile.status is StageStatus.OK
    # The stub simulator prints no checker line, so the run cannot pass.
    assert res.verdict is Verdict.UNKNOWN and res.failure_category is FailureCategory.CHECKER_INCONCLUSIVE


def test_nonzero_version_probe_exit_is_recorded_not_blocking(tmp_path, candidate):
    tool = _stub(tmp_path / "tool", VERSION_NONZERO)
    res = _verify(tmp_path, candidate("correct"), find_tools(tool, tool))
    assert res.compile.version_probe.exit_code == 1 and res.compile.tool_version == "Stub Icarus Verilog version 0"
    assert res.compile.status is StageStatus.OK
