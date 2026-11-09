"""Bounded subprocess runner.

The only place in the package that starts child processes. Guarantees:
argument-list execution (never a shell), explicit working directory, an explicit
minimal environment (the parent environment is never inherited, so provider
keys cannot leak), a wall-clock timeout, and stdout/stderr capture that is
bounded *while the process runs*.

Cleanup (POSIX): the child leads its own process group. On every exit path --
normal completion, timeout, or an exception such as KeyboardInterrupt -- the
whole group is SIGKILLed *before* the leader is reaped, so the group id cannot
have been reused, then the leader is reaped and the capture threads joined.
Descendants that leave the group (setsid) are outside this guarantee.

Capture failures (log file cannot be opened/written, capture thread did not
finish) are reported in ``ProcessResult.capture_errors``; they never pass silently.
"""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import BinaryIO, Mapping, Sequence

from verilog_copilot.models import ProcessResult

_READ_CHUNK = 64 * 1024
_PIPE_DRAIN_GRACE_S = 5.0
_POSIX = os.name == "posix"
_HAVE_WAITID = _POSIX and hasattr(os, "waitid") and hasattr(os, "WNOWAIT")


def minimal_env(path_dirs: Sequence[str] = ()) -> dict[str, str]:
    """Build a small child environment from scratch.

    ``path_dirs`` (e.g. the directory holding ``iverilog``) are placed before
    the standard system directories. Nothing else from ``os.environ`` is copied.
    """
    dirs: list[str] = []
    for d in [*path_dirs, "/usr/bin", "/bin"]:
        if d and d not in dirs:
            dirs.append(d)
    return {"PATH": os.pathsep.join(dirs), "LC_ALL": "C", "LANG": "C"}


class _BoundedPump(threading.Thread):
    """Copy a pipe to a file, keeping at most ``limit`` bytes.

    Always drains the pipe to EOF -- even after the log file failed to open or a
    write failed -- so the child never blocks on a full pipe. Failures are
    recorded in ``error`` instead of being lost inside the thread.
    """

    def __init__(self, stream: BinaryIO, dest: Path, limit: int) -> None:
        super().__init__(daemon=True)
        self._stream = stream
        self._dest = dest
        self._limit = limit
        self.total_bytes = 0
        self.written_bytes = 0
        self.error: str | None = None

    def _record(self, what: str, exc: BaseException) -> None:
        if self.error is None:
            self.error = f"{what} {self._dest}: {type(exc).__name__}: {exc}"

    def _write_chunk(self, out: BinaryIO, data: bytes) -> None:
        out.write(data)  # separate method so tests can simulate write failures

    def run(self) -> None:
        out: BinaryIO | None = None
        try:
            out = open(self._dest, "wb")
        except Exception as exc:  # recorded, never swallowed silently
            self._record("cannot open log", exc)
        try:
            fd = self._stream.fileno()
            while True:
                try:
                    chunk = os.read(fd, _READ_CHUNK)
                except OSError as exc:
                    self._record("cannot read pipe for", exc)
                    break
                if not chunk:
                    break
                self.total_bytes += len(chunk)
                room = self._limit - self.written_bytes
                if out is not None and room > 0:
                    piece = chunk[:room]
                    try:
                        self._write_chunk(out, piece)
                        self.written_bytes += len(piece)
                    except Exception as exc:
                        self._record("cannot write log", exc)
                        self._close(out)
                        out = None  # keep draining, stop writing
        finally:
            if out is not None:
                self._close(out)
            try:
                self._stream.close()
            except OSError:
                pass

    def _close(self, out: BinaryIO) -> None:
        try:
            out.close()
        except Exception as exc:
            self._record("cannot close log", exc)

    @property
    def truncated(self) -> bool:
        return self.total_bytes > self.written_bytes


def _kill_tree(proc: subprocess.Popen) -> None:
    if _POSIX:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    else:  # pragma: no cover - Windows path is untested in M1
        try:
            proc.kill()
        except OSError:
            pass


def _wait_for_leader_exit(proc: subprocess.Popen, timeout_s: float) -> bool:
    """Wait until the leader exits WITHOUT reaping it (so its process-group id
    stays reserved for the cleanup kill). Returns False on timeout."""
    if not _HAVE_WAITID:  # pragma: no cover - fallback reaps immediately
        try:
            proc.wait(timeout=timeout_s)
            return True
        except subprocess.TimeoutExpired:
            return False
    deadline = time.monotonic() + timeout_s
    delay = 0.001
    while True:
        try:
            info = os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        except ChildProcessError:
            return True
        if info is not None and info.si_pid == proc.pid:
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(delay, remaining))
        delay = min(delay * 2, 0.02)


def _touch_logs(paths: Sequence[Path]) -> list[str]:
    errors = []
    for p in paths:
        try:
            Path(p).write_bytes(b"")
        except OSError as exc:
            errors.append(f"cannot create log {p}: {type(exc).__name__}: {exc}")
    return errors


def run_process(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout_s: float,
    stdout_path: Path,
    stderr_path: Path,
    max_log_bytes: int,
    env: Mapping[str, str] | None = None,
) -> ProcessResult:
    """Run ``argv`` with bounded time and output.

    Child failures and spawn problems (missing executable, permission) are
    reported in the result. Exceptions raised in the caller's thread while
    waiting (e.g. KeyboardInterrupt) propagate *after* the process group has been
    killed, the leader reaped, and the capture threads joined.
    """
    argv = [str(a) for a in argv]
    if not argv:
        raise ValueError("argv must not be empty")
    if timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    if max_log_bytes < 0:
        raise ValueError("max_log_bytes must be non-negative")
    child_env = dict(env) if env is not None else minimal_env()

    start = time.monotonic()
    try:
        proc = subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=_POSIX,
        )
    except OSError as exc:
        return ProcessResult(
            argv=argv, cwd=str(cwd), exit_code=None, signal=None,
            duration_s=time.monotonic() - start, timed_out=False,
            stdout_path=str(stdout_path), stderr_path=str(stderr_path),
            stdout_bytes=0, stderr_bytes=0,
            stdout_truncated=False, stderr_truncated=False,
            spawn_error=f"{type(exc).__name__}: {exc}",
            capture_errors=_touch_logs([stdout_path, stderr_path]),
        )

    assert proc.stdout is not None and proc.stderr is not None
    pumps: list[_BoundedPump] = []
    timed_out = False
    try:
        for stream, dest in ((proc.stdout, stdout_path), (proc.stderr, stderr_path)):
            pump = _BoundedPump(stream, dest, max_log_bytes)
            pump.start()
            pumps.append(pump)
        timed_out = not _wait_for_leader_exit(proc, timeout_s)
    finally:
        # Every exit path: kill the group while the leader is still unreaped,
        # then reap, then drain/join the capture threads.
        _kill_tree(proc)
        proc.wait()
        duration = time.monotonic() - start
        for pump in pumps:
            pump.join(timeout=_PIPE_DRAIN_GRACE_S)
        for stream in (proc.stdout, proc.stderr):
            if not any(p._stream is stream for p in pumps):
                stream.close()

    capture_errors = [p.error for p in pumps if p.error]
    capture_errors += [
        f"capture of {p._dest} did not finish (a process outside the group may hold the pipe)"
        for p in pumps if p.is_alive()
    ]
    rc = proc.returncode
    out_pump, err_pump = pumps
    return ProcessResult(
        argv=argv,
        cwd=str(cwd),
        exit_code=rc if rc is not None and rc >= 0 else None,
        signal=-rc if rc is not None and rc < 0 else None,
        duration_s=round(duration, 6),
        timed_out=timed_out,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        stdout_bytes=out_pump.total_bytes,
        stderr_bytes=err_pump.total_bytes,
        stdout_truncated=out_pump.truncated,
        stderr_truncated=err_pump.truncated,
        capture_errors=capture_errors,
    )
