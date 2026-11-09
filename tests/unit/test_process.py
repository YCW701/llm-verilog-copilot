"""Bounded process runner tests. Use the Python interpreter as the child, so no
Verilog tools are required."""

from __future__ import annotations

import errno
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from verilog_copilot.tools import process
from verilog_copilot.tools.process import minimal_env, run_process

PY = sys.executable


def _run(tmp_path, code, *, timeout_s=10.0, max_log_bytes=1 << 20, env=None, cwd=None):
    return run_process(
        [PY, "-c", code],
        cwd=cwd or tmp_path,
        timeout_s=timeout_s,
        stdout_path=tmp_path / "out.log",
        stderr_path=tmp_path / "err.log",
        max_log_bytes=max_log_bytes,
        env=env,
    )


def test_success_captures_output_and_exit_code(tmp_path):
    res = _run(tmp_path, "import sys; print('hello'); print('oops', file=sys.stderr)")
    assert res.exit_code == 0 and res.signal is None and not res.timed_out
    assert (tmp_path / "out.log").read_text() == "hello\n"
    assert (tmp_path / "err.log").read_text() == "oops\n"
    assert res.argv[0] == PY and res.duration_s > 0


def test_nonzero_exit_is_reported(tmp_path):
    res = _run(tmp_path, "raise SystemExit(7)")
    assert res.exit_code == 7 and not res.timed_out and res.spawn_error is None


def test_missing_executable_is_spawn_error_not_exception(tmp_path):
    res = run_process(
        [str(tmp_path / "no-such-tool")], cwd=tmp_path, timeout_s=5,
        stdout_path=tmp_path / "o", stderr_path=tmp_path / "e", max_log_bytes=1024,
    )
    assert res.exit_code is None and res.spawn_error and "FileNotFoundError" in res.spawn_error


def test_timeout_kills_entire_process_tree(tmp_path):
    pid_file = tmp_path / "grandchild.pid"
    code = (
        "import subprocess, sys, time\n"
        f"p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        f"open({str(pid_file)!r}, 'w').write(str(p.pid))\n"
        "time.sleep(60)\n"
    )
    t0 = time.monotonic()
    res = _run(tmp_path, code, timeout_s=1.5)
    elapsed = time.monotonic() - t0
    assert res.timed_out and res.exit_code is None and res.signal is not None
    assert elapsed < 10, "runner did not return promptly after the timeout"
    grandchild = int(pid_file.read_text())
    # The grandchild may linger briefly as a zombie until init reaps it.
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(grandchild, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        pytest.fail(f"grandchild {grandchild} survived the timeout kill")


def test_output_is_bounded_while_running(tmp_path):
    # Writes 5 MiB but only 4 KiB may be kept; the child must not block.
    code = "import sys; sys.stdout.write('x' * (5 * 1024 * 1024))"
    res = _run(tmp_path, code, max_log_bytes=4096)
    assert res.exit_code == 0
    assert res.stdout_truncated and not res.stderr_truncated
    assert res.stdout_bytes == 5 * 1024 * 1024
    assert (tmp_path / "out.log").stat().st_size == 4096


def test_parent_environment_is_not_inherited(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_PROVIDER_API_KEY", "sk-should-never-leak")
    res = _run(tmp_path, "import os; print(sorted(os.environ))")
    assert res.exit_code == 0
    out = (tmp_path / "out.log").read_text()
    assert "FAKE_PROVIDER_API_KEY" not in out
    assert "sk-should-never-leak" not in out


def test_minimal_env_contents():
    env = minimal_env(["/opt/tools/bin"])
    assert set(env) == {"PATH", "LC_ALL", "LANG"}
    assert env["PATH"].split(os.pathsep)[0] == "/opt/tools/bin"


def test_paths_with_spaces_and_shell_metacharacters_are_literal(tmp_path):
    odd = tmp_path / "dir with spaces; $(echo pwned)"
    odd.mkdir()
    res = run_process(
        [PY, "-c", "import os, sys; print(os.getcwd()); print(sys.argv[1])", "arg with $HOME and ; rm"],
        cwd=odd, timeout_s=10, stdout_path=odd / "o.log", stderr_path=odd / "e.log", max_log_bytes=4096,
    )
    assert res.exit_code == 0
    lines = (odd / "o.log").read_text().splitlines()
    assert os.path.realpath(lines[0]) == os.path.realpath(odd)
    assert lines[1] == "arg with $HOME and ; rm"


@pytest.mark.parametrize("kwargs", [{"timeout_s": 0}, {"max_log_bytes": -1}])
def test_invalid_limits_rejected(tmp_path, kwargs):
    base = dict(cwd=tmp_path, timeout_s=1, stdout_path=tmp_path / "o", stderr_path=tmp_path / "e", max_log_bytes=10)
    base.update(kwargs)
    with pytest.raises(ValueError):
        run_process([PY, "-c", "pass"], **base)


# --- M1 correction regressions (review findings M1-C3 and M1-I1) ---------------------

SRC_DIR = str(Path(__file__).resolve().parents[2] / "src")


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _wait_gone(pid: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _alive(pid):
            return True
        time.sleep(0.05)
    return False


def _force_kill(pid: int | None) -> None:
    if pid is None:
        return
    try:
        os.kill(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def _read_pid(path, timeout: float = 10.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            text = path.read_text().strip()
            if text:
                return int(text)
        except FileNotFoundError:
            pass
        time.sleep(0.02)
    raise AssertionError(f"pid file {path} was never written")


def _live_pumps():
    return [t for t in threading.enumerate() if isinstance(t, process._BoundedPump) and t.is_alive()]


def test_sigint_to_caller_kills_child_and_propagates(tmp_path):
    """Review probe 1: SIGINT interrupts the runner; the child must not survive and
    the interruption must surface as KeyboardInterrupt, not a design verdict."""
    pid_file = tmp_path / "sleeper.pid"
    helper = tmp_path / "helper.py"
    helper.write_text(
        "import sys\n"
        f"sys.path.insert(0, {SRC_DIR!r})\n"
        "from pathlib import Path\n"
        "from verilog_copilot.tools.process import run_process\n"
        f"work = Path({str(tmp_path)!r})\n"
        f"code = \"import os, time; open({str(pid_file)!r}, 'w').write(str(os.getpid())); time.sleep(60)\"\n"
        "try:\n"
        "    run_process([sys.executable, '-c', code], cwd=work, timeout_s=60,\n"
        "                stdout_path=work / 'o.log', stderr_path=work / 'e.log', max_log_bytes=4096)\n"
        "except KeyboardInterrupt:\n"
        "    print('INTERRUPTED', flush=True)\n"
        "    sys.exit(130)\n"
        "print('NOT INTERRUPTED', flush=True)\n"
    )
    runner = subprocess.Popen([PY, str(helper)], stdout=subprocess.PIPE, text=True)
    sleeper = None
    try:
        sleeper = _read_pid(pid_file)
        runner.send_signal(signal.SIGINT)
        out, _ = runner.communicate(timeout=15)
        assert runner.returncode == 130 and "INTERRUPTED" in out
        assert _wait_gone(sleeper), f"child {sleeper} survived SIGINT to the runner"
    finally:
        _force_kill(sleeper)
        if runner.poll() is None:
            runner.kill()
            runner.wait()


def test_successful_leader_does_not_leave_redirected_descendant(tmp_path):
    """Review probe 2: leader exits 0 after starting a descendant whose streams are
    redirected to DEVNULL (so it does not hold the capture pipes open)."""
    pid_file = tmp_path / "descendant.pid"
    code = (
        "import subprocess, sys\n"
        "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'],\n"
        "                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        f"open({str(pid_file)!r}, 'w').write(str(p.pid))\n"
    )
    descendant = None
    try:
        res = _run(tmp_path, code, timeout_s=20)
        descendant = _read_pid(pid_file)
        assert res.exit_code == 0 and not res.timed_out and res.capture_errors == []
        assert _wait_gone(descendant), f"descendant {descendant} survived after the leader exited"
    finally:
        _force_kill(descendant)


def test_exit_code_survives_post_exit_group_cleanup(tmp_path):
    res = _run(tmp_path, "raise SystemExit(5)")
    assert res.exit_code == 5 and res.signal is None


def test_log_open_failure_is_reported(tmp_path):
    """Review probe: stderr destination is a directory."""
    err_dir = tmp_path / "stderr-is-a-dir"
    err_dir.mkdir()
    res = run_process(
        [PY, "-c", "import sys; print('out'); print('err' * 1000, file=sys.stderr)"],
        cwd=tmp_path, timeout_s=10, stdout_path=tmp_path / "o.log", stderr_path=err_dir, max_log_bytes=4096,
    )
    assert res.exit_code == 0
    assert len(res.capture_errors) == 1 and "cannot open log" in res.capture_errors[0]
    assert str(err_dir) in res.capture_errors[0]
    assert res.stderr_bytes == 3001 and res.stderr_truncated  # drained, nothing kept
    assert (tmp_path / "o.log").read_text() == "out\n"
    assert _live_pumps() == []


def test_log_write_failure_is_reported_and_child_not_blocked(tmp_path, monkeypatch):
    def failing_write(self, out, data):
        raise OSError(errno.ENOSPC, "No space left on device (simulated)")

    monkeypatch.setattr(process._BoundedPump, "_write_chunk", failing_write)
    # 5 MiB exceeds any pipe buffer: if the pump stopped draining, this would hang.
    res = _run(tmp_path, "import sys; sys.stdout.write('x' * (5 * 1024 * 1024))", timeout_s=20)
    assert res.exit_code == 0 and not res.timed_out
    assert any("cannot write log" in e and "No space left" in e for e in res.capture_errors)
    assert res.stdout_bytes == 5 * 1024 * 1024
    assert _live_pumps() == []


def test_spawn_error_with_unwritable_log_paths_does_not_raise(tmp_path):
    bad = tmp_path / "dir"
    bad.mkdir()
    res = run_process([str(tmp_path / "no-such-tool")], cwd=tmp_path, timeout_s=5,
                      stdout_path=bad, stderr_path=bad, max_log_bytes=1024)
    assert res.spawn_error and len(res.capture_errors) == 2


def test_no_capture_threads_left_after_normal_runs(tmp_path):
    for i in range(3):
        _run(tmp_path, f"print({i})")
    assert _live_pumps() == []
