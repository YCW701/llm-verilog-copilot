"""Shared paths and the Icarus availability gate for integration tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
ADDER4_CANDIDATES = FIXTURES / "adder4" / "candidates"

HAVE_ICARUS = shutil.which("iverilog") is not None and shutil.which("vvp") is not None
requires_icarus = pytest.mark.skipif(
    not HAVE_ICARUS, reason="SKIPPED: iverilog and/or vvp not found on PATH"
)


@pytest.fixture
def candidate():
    def _get(name: str) -> Path:
        return ADDER4_CANDIDATES / f"{name}.v"
    return _get
