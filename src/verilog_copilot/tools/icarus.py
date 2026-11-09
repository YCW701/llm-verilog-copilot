"""Icarus Verilog backend details: tool discovery, versions, command lines.

Only fixed, harness-chosen flags are used. Candidates cannot pick flags,
include paths, output names, or the top-level module.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from verilog_copilot.models import ProcessResult
from verilog_copilot.tools.process import minimal_env, run_process

VERSION_PROBE_TIMEOUT_S = 10.0
VERSION_PROBE_MAX_BYTES = 64 * 1024


@dataclass(frozen=True)
class IcarusTools:
    iverilog: str | None
    vvp: str | None

    @property
    def missing(self) -> list[str]:
        return [name for name, path in (("iverilog", self.iverilog), ("vvp", self.vvp)) if path is None]

    def child_env(self) -> dict[str, str]:
        dirs = sorted({os.path.dirname(p) for p in (self.iverilog, self.vvp) if p})
        return minimal_env(dirs)


def _resolve(explicit: str | None, name: str) -> str | None:
    if explicit is not None:
        p = Path(explicit)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p.resolve())
        return None
    found = shutil.which(name)
    return str(Path(found).resolve()) if found else None


def find_tools(iverilog: str | None = None, vvp: str | None = None) -> IcarusTools:
    """Locate the tools from explicit paths, else from PATH. Missing tools are None."""
    return IcarusTools(iverilog=_resolve(iverilog, "iverilog"), vvp=_resolve(vvp, "vvp"))


@dataclass(frozen=True)
class VersionProbe:
    """Result of ``<tool> -V``.

    ``error`` is set when the probe's evidence is unusable (spawn failure,
    capture failure, timeout, signal termination, or unreadable logs); callers
    must not proceed to a verdict in that case. ``version`` is None both on error
    and when the probe was recorded cleanly but printed no recognizable version
    line; ``error is None`` distinguishes the latter. A non-zero exit status is
    recorded in ``process`` but does not by itself set ``error``.
    """

    process: ProcessResult
    version: str | None
    error: str | None


def probe_version(executable: str, work_dir: Path, env: dict[str, str]) -> VersionProbe:
    """Run ``<tool> -V`` under the bounded runner and return its evidence."""
    name = Path(executable).name
    res = run_process(
        [executable, "-V"],
        cwd=work_dir,
        timeout_s=VERSION_PROBE_TIMEOUT_S,
        stdout_path=work_dir / f"{name}.version.stdout.log",
        stderr_path=work_dir / f"{name}.version.stderr.log",
        max_log_bytes=VERSION_PROBE_MAX_BYTES,
        env=env,
    )
    if res.spawn_error:
        return VersionProbe(res, None, f"could not start: {res.spawn_error}")
    if res.capture_errors:
        return VersionProbe(res, None, "output could not be fully recorded: " + "; ".join(res.capture_errors))
    if res.timed_out:
        return VersionProbe(res, None, f"exceeded {VERSION_PROBE_TIMEOUT_S}s; its process group was killed")
    if res.signal is not None:
        return VersionProbe(res, None, f"terminated by signal {res.signal}")
    try:
        text = Path(res.stdout_path).read_text(errors="replace") + Path(res.stderr_path).read_text(errors="replace")
    except OSError as exc:
        return VersionProbe(res, None, f"version log could not be read: {exc}")
    for line in text.splitlines():
        if "version" in line.lower():
            return VersionProbe(res, line.strip(), None)
    return VersionProbe(res, None, None)


def compile_argv(
    iverilog: str, *, language_flag: str, top: str, output: str, sources: Sequence[str]
) -> list[str]:
    return [iverilog, language_flag, "-Wall", "-s", top, "-o", output, *sources]


def simulate_argv(vvp: str, *, compiled: str, plusargs: Sequence[str]) -> list[str]:
    # -n: treat $stop as $finish so a stray $stop cannot open an interactive prompt.
    return [vvp, "-n", compiled, *plusargs]
