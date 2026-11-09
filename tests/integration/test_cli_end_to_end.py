"""Run the real CLI as a subprocess (``python -m verilog_copilot``)."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from conftest import REPO_ROOT, requires_icarus

pytestmark = [pytest.mark.integration, requires_icarus]


def _cli(*args):
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    return subprocess.run([sys.executable, "-m", "verilog_copilot", *args],
                          capture_output=True, text=True, env=env, timeout=60)


def test_cli_pass_writes_artifacts(tmp_path, candidate):
    out = tmp_path / "run dir"
    proc = _cli("verify", "--rtl", str(candidate("correct")), "--task", "adder4", "--output", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "verdict:   pass" in proc.stdout
    result = json.loads((out / "verification.json").read_text())
    manifest = json.loads((out / "manifest.json").read_text())
    assert result["verdict"] == "pass" and result["schema_version"] == "3"
    assert result["candidate_origin"] == "team_authored" and result["rtl_screen"] == "ok"
    assert manifest["tools"]["iverilog"]["version"] and manifest["code_sha256"]
    assert (out / "candidate.v").is_file()


def test_cli_hang_exit_code_and_refuses_rerun(tmp_path, candidate):
    out = tmp_path / "hang"
    # hang.v (which floods via $display) is now rejected by the RTL screen; the silent
    # variant exercises the timeout and process-group kill through the CLI.
    args = ("verify", "--rtl", str(candidate("hang_silent")), "--task", "adder4", "--output", str(out),
            "--sim-timeout", "2", "--max-log-bytes", "65536")
    proc = _cli(*args)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert json.loads((out / "verification.json").read_text())["failure_category"] == "simulation_timeout"
    again = _cli(*args)
    assert again.returncode == 2 and "refusing to overwrite" in again.stderr


@pytest.mark.parametrize("name,code,category", [
    ("wrong_behavior", 1, "test_mismatch"),
    ("syntax_error", 1, "compile_error"),
    # Screen-rejected before compilation (supported-path classification changed in
    # the M1 correction; early_finish was exit 3 / checker_inconclusive before).
    ("fake_pass", 1, "candidate_policy_violation"),
    ("early_finish", 1, "candidate_policy_violation"),
    ("hang", 1, "candidate_policy_violation"),
    ("nonce_forgery", 1, "candidate_policy_violation"),
    ("hierarchical_tamper", 1, "candidate_policy_violation"),
])
def test_cli_exit_codes(tmp_path, candidate, name, code, category):
    out = tmp_path / "r"
    proc = _cli("verify", "--rtl", str(candidate(name)), "--task", "adder4", "--output", str(out))
    assert proc.returncode == code, proc.stdout + proc.stderr
    assert json.loads((out / "verification.json").read_text())["failure_category"] == category
