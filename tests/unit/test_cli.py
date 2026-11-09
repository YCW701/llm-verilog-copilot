"""CLI behavior that does not need Icarus installed."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time

import pytest

from conftest import REPO_ROOT
from verilog_copilot.cli import EXIT_UNKNOWN, EXIT_USAGE, main


def test_existing_output_is_refused(tmp_path, candidate):
    out = tmp_path / "run"
    out.mkdir()
    (out / "keep.txt").write_text("precious")
    rc = main(["verify", "--rtl", str(candidate("correct")), "--task", "adder4", "--output", str(out)])
    assert rc == EXIT_USAGE
    assert sorted(p.name for p in out.iterdir()) == ["keep.txt"]


def test_missing_rtl_is_usage_error(tmp_path):
    rc = main(["verify", "--rtl", str(tmp_path / "nope.v"), "--task", "adder4", "--output", str(tmp_path / "r")])
    assert rc == EXIT_USAGE and not (tmp_path / "r").exists()


def test_unknown_task_rejected_by_parser(tmp_path, candidate):
    with pytest.raises(SystemExit) as exc:
        main(["verify", "--rtl", str(candidate("correct")), "--task", "bogus", "--output", str(tmp_path / "r")])
    assert exc.value.code == 2


@pytest.mark.parametrize("flag,value", [("--sim-timeout", "0"), ("--sim-timeout", "-1"),
                                        ("--compile-timeout", "abc"), ("--max-log-bytes", "10")])
def test_invalid_limits_rejected(tmp_path, candidate, flag, value):
    with pytest.raises(SystemExit) as exc:
        main(["verify", "--rtl", str(candidate("correct")), "--task", "adder4",
              "--output", str(tmp_path / "r"), flag, value])
    assert exc.value.code == 2


def test_missing_tool_is_infrastructure_error_not_design_failure(tmp_path, candidate):
    out = tmp_path / "run"
    rc = main(["verify", "--rtl", str(candidate("correct")), "--task", "adder4", "--output", str(out),
               "--iverilog", str(tmp_path / "missing-iverilog"), "--vvp", str(tmp_path / "missing-vvp")])
    assert rc == EXIT_UNKNOWN
    result = json.loads((out / "verification.json").read_text())
    assert result["verdict"] == "unknown"
    assert result["failure_category"] == "missing_tool"
    assert result["compile"]["status"] == "tool_error"
    assert result["simulation"]["status"] == "not_run"
    assert (out / "manifest.json").is_file()


def test_unwritable_output_location_is_usage_error_not_design_failure(tmp_path, candidate):
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("file, not directory")
    rc = main(["verify", "--rtl", str(candidate("correct")), "--task", "adder4",
               "--output", str(blocker / "run")])
    assert rc == EXIT_USAGE


def test_unexpected_internal_error_is_unknown_not_design_failure(tmp_path, candidate, monkeypatch, capsys):
    import verilog_copilot.cli as cli

    def boom(*_a, **_k):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(cli, "verify", boom)
    rc = main(["verify", "--rtl", str(candidate("correct")), "--task", "adder4", "--output", str(tmp_path / "r")])
    assert rc == EXIT_UNKNOWN
    assert "internal error: RuntimeError: disk on fire" in capsys.readouterr().err


def test_keyboard_interrupt_is_exit_130_without_verdict(tmp_path, candidate, monkeypatch, capsys):
    import verilog_copilot.cli as cli

    def interrupted(*_a, **_k):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "verify", interrupted)
    out = tmp_path / "r"
    rc = main(["verify", "--rtl", str(candidate("correct")), "--task", "adder4", "--output", str(out)])
    assert rc == cli.EXIT_INTERRUPTED == 130
    assert not (out / "verification.json").exists()
    assert "interrupted" in capsys.readouterr().err


@pytest.mark.skipif(os.name != "posix", reason="SKIPPED: POSIX signals and shell stubs required")
@pytest.mark.parametrize("signame", ["SIGTERM", "SIGHUP"])
def test_cli_termination_signal_kills_simulator_and_writes_no_verdict(tmp_path, candidate, signame):
    """SIGTERM/SIGHUP to the CLI must run the runner's cleanup (the simulator lives in
    its own session, so it never receives terminal signals itself)."""
    sig = getattr(signal, signame)
    pid_file = tmp_path / "vvp.pid"
    iverilog = tmp_path / "iverilog-stub"
    iverilog.write_text('#!/bin/sh\nif [ "$1" = "-V" ]; then echo "Stub version 0"; exit 0; fi\n'
                        'while [ $# -gt 0 ]; do if [ "$1" = "-o" ]; then : > "$2"; fi; shift; done\nexit 0\n')
    vvp = tmp_path / "vvp-stub"
    vvp.write_text('#!/bin/sh\nif [ "$1" = "-V" ]; then echo "Stub version 0"; exit 0; fi\n'
                   f"echo $$ > '{pid_file}'\nexec /bin/sleep 60\n")
    for stub in (iverilog, vvp):
        stub.chmod(0o755)
    out = tmp_path / "run"
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    cli = subprocess.Popen(
        [sys.executable, "-m", "verilog_copilot", "verify", "--rtl", str(candidate("correct")), "--task", "adder4",
         "--output", str(out), "--iverilog", str(iverilog), "--vvp", str(vvp), "--sim-timeout", "120"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
    )
    sim_pid = None
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not (pid_file.exists() and pid_file.read_text().strip()):
            time.sleep(0.02)
        sim_pid = int(pid_file.read_text())
        cli.send_signal(sig)
        _, err = cli.communicate(timeout=15)
        assert cli.returncode == 128 + sig, err
        assert "no verdict written" in err
        assert not (out / "verification.json").exists()
        gone_by = time.monotonic() + 5
        while time.monotonic() < gone_by:
            try:
                os.kill(sim_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            pytest.fail(f"simulator {sim_pid} survived {signame} to the CLI")
    finally:
        if sim_pid is not None:
            try:
                os.kill(sim_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if cli.poll() is None:
            cli.kill()
            cli.wait()


def test_cli_restores_signal_handlers(tmp_path, candidate):
    before = signal.getsignal(signal.SIGTERM)
    main(["verify", "--rtl", str(candidate("correct")), "--task", "adder4", "--output", str(tmp_path / "r"),
          "--iverilog", str(tmp_path / "missing"), "--vvp", str(tmp_path / "missing")])
    assert signal.getsignal(signal.SIGTERM) is before
