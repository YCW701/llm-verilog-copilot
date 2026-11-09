"""Command-line interface for the M1 offline verification harness.

Exit codes:
  0  functional pass confirmed by the trusted checker
  1  definite design failure (compile error or checker-reported mismatch)
  2  usage/configuration error (bad arguments, unknown task, existing output)
  3  verdict unknown (timeout, inconclusive checker, missing tool, infrastructure)
  130 interrupted by Ctrl-C (SIGINT); 143 SIGTERM; 129 SIGHUP. Child process
      groups are killed before exiting and no verdict is written. (SIGKILL to the
      harness cannot be intercepted; its children would then need manual cleanup.)

The CLI executes only team-authored RTL (CandidateOrigin.TEAM_AUTHORED). Running
model-generated RTL is blocked until an execution-safety policy is adopted.
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import signal
import sys
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from verilog_copilot import __version__
from verilog_copilot.benchmarks import local_fixtures
from verilog_copilot.models import SCHEMA_VERSION, CandidateOrigin, Verdict, VerificationResult, to_jsonable
from verilog_copilot.storage import OutputExistsError, create_run_dir, write_json_exclusive
from verilog_copilot.tools.icarus import find_tools
from verilog_copilot.tools.simulation import SimulationLimits, verify

EXIT_PASS, EXIT_FAIL, EXIT_USAGE, EXIT_UNKNOWN, EXIT_INTERRUPTED = 0, 1, 2, 3, 130
_TERMINATION_SIGNALS = tuple(getattr(signal, n) for n in ("SIGTERM", "SIGHUP") if hasattr(signal, n))
_MAX_TIMEOUT_S = 3600.0
_MIN_LOG_BYTES, _MAX_LOG_BYTES = 1024, 256 * 1024 * 1024


class _TerminationRequested(BaseException):
    """Raised from a SIGTERM/SIGHUP handler so ``finally`` cleanup (killing the
    child process group) runs instead of Python exiting immediately. Deliberately
    not an ``Exception`` so the internal-error handler cannot turn it into exit 3."""

    def __init__(self, signum: int) -> None:
        super().__init__(signum)
        self.signum = signum


def _raise_termination(signum: int, _frame) -> None:
    raise _TerminationRequested(signum)


def _timeout(value: str) -> float:
    try:
        t = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {value!r}") from None
    if not 0 < t <= _MAX_TIMEOUT_S:
        raise argparse.ArgumentTypeError(f"timeout must be in (0, {_MAX_TIMEOUT_S:g}] seconds")
    return t


def _log_bytes(value: str) -> int:
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an integer: {value!r}") from None
    if not _MIN_LOG_BYTES <= n <= _MAX_LOG_BYTES:
        raise argparse.ArgumentTypeError(f"must be in [{_MIN_LOG_BYTES}, {_MAX_LOG_BYTES}] bytes")
    return n


def build_parser() -> argparse.ArgumentParser:
    defaults = SimulationLimits()
    parser = argparse.ArgumentParser(
        prog="verilog-copilot",
        description="LLM Copilot for Verilog Design -- M1 offline verification harness.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser(
        "verify",
        help="Compile and simulate a team-authored RTL file against a trusted fixture checker.",
        description="Only team-authored RTL may be verified. Candidates are screened for "
                    "checker-interfering constructs (system tasks, hierarchical references, "
                    "force/release/defparam, compiler directives other than `timescale) before compilation.",
    )
    v.add_argument("--rtl", required=True, type=Path,
                   help="Team-authored candidate Verilog file (read only; a copy is verified).")
    v.add_argument("--task", required=True, choices=local_fixtures.task_ids(), help="Registered fixture task ID.")
    v.add_argument("--output", required=True, type=Path, help="New run directory to create (must not exist).")
    v.add_argument("--compile-timeout", type=_timeout, default=defaults.compile_timeout_s, metavar="SECONDS",
                   help=f"iverilog wall-clock limit (default {defaults.compile_timeout_s:g})")
    v.add_argument("--sim-timeout", type=_timeout, default=defaults.simulation_timeout_s, metavar="SECONDS",
                   help=f"vvp wall-clock limit (default {defaults.simulation_timeout_s:g})")
    v.add_argument("--max-log-bytes", type=_log_bytes, default=defaults.max_log_bytes, metavar="BYTES",
                   help=f"cap per captured stream (default {defaults.max_log_bytes})")
    v.add_argument("--iverilog", default=None, metavar="PATH", help="Explicit iverilog executable (default: PATH lookup).")
    v.add_argument("--vvp", default=None, metavar="PATH", help="Explicit vvp executable (default: PATH lookup).")
    return parser


def _code_hashes() -> dict[str, str]:
    pkg = Path(__file__).resolve().parent
    return {
        str(p.relative_to(pkg)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(pkg.rglob("*.py"))
    }


def _manifest(argv: Sequence[str], args: argparse.Namespace, limits: SimulationLimits,
              result: VerificationResult, tools) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "package_version": __version__,
        "command": ["verilog-copilot", *argv],
        "python": sys.version,
        "platform": platform.platform(),
        "task_id": args.task,
        "limits": asdict(limits),
        "tools": {
            "iverilog": {"path": tools.iverilog, "version": result.compile.tool_version},
            "vvp": {"path": tools.vvp, "version": result.simulation.tool_version},
        },
        "trusted_files": to_jsonable(result.trusted_files),
        "candidate_source": to_jsonable(result.candidate_source),
        "code_sha256": _code_hashes(),
        "code_revision": None,  # repository is not under version control yet
    }


def _cmd_verify(args: argparse.Namespace, argv: Sequence[str]) -> int:
    bundle = local_fixtures.get_bundle(args.task)
    if not args.rtl.is_file():
        print(f"error: RTL file not found: {args.rtl}", file=sys.stderr)
        return EXIT_USAGE
    try:
        run_dir = create_run_dir(args.output)
    except OutputExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except OSError as exc:
        print(f"error: cannot create output directory {args.output}: {exc}", file=sys.stderr)
        return EXIT_USAGE

    limits = SimulationLimits(
        compile_timeout_s=args.compile_timeout,
        simulation_timeout_s=args.sim_timeout,
        max_log_bytes=args.max_log_bytes,
    )
    tools = find_tools(args.iverilog, args.vvp)
    try:
        result = verify(args.rtl, bundle, limits, run_dir, tools, origin=CandidateOrigin.TEAM_AUTHORED)
    except KeyboardInterrupt:
        print(f"interrupted: run incomplete, no verdict written; partial artifacts in {run_dir}", file=sys.stderr)
        return EXIT_INTERRUPTED
    except _TerminationRequested as exc:
        print(f"terminated by signal {exc.signum}: run incomplete, no verdict written; "
              f"partial artifacts in {run_dir}", file=sys.stderr)
        return 128 + exc.signum
    write_json_exclusive(run_dir / "verification.json", to_jsonable(result))
    write_json_exclusive(run_dir / "manifest.json", _manifest(argv, args, limits, result, tools))

    print(f"task:      {result.task_id}")
    print(f"verdict:   {result.verdict.value}")
    print(f"category:  {result.failure_category.value}")
    print(f"screen:    {result.rtl_screen.value}")
    print(f"compile:   {result.compile.status.value}")
    print(f"simulate:  {result.simulation.status.value}")
    print(f"message:   {result.message}")
    for violation in result.policy_violations:
        print(f"  policy:  {violation}")
    print(f"artifacts: {run_dir}")
    if result.verdict is Verdict.PASS:
        return EXIT_PASS
    if result.verdict is Verdict.FAIL:
        return EXIT_FAIL
    return EXIT_UNKNOWN


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    previous = {}
    if threading.current_thread() is threading.main_thread():
        for signum in _TERMINATION_SIGNALS:
            previous[signum] = signal.signal(signum, _raise_termination)
    try:
        if args.command == "verify":
            return _cmd_verify(args, argv)
    except KeyboardInterrupt:
        print("interrupted: run incomplete, no verdict written", file=sys.stderr)
        return EXIT_INTERRUPTED
    except _TerminationRequested as exc:
        print(f"terminated by signal {exc.signum}: run incomplete", file=sys.stderr)
        return 128 + exc.signum
    except Exception as exc:  # never let a crash look like exit 1 (design failure)
        print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_UNKNOWN
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    return EXIT_USAGE  # pragma: no cover - argparse enforces a command
